"""Core proxy logic — the FastAPI application that intercepts LLM API calls."""

from __future__ import annotations

import json
import time
from typing import Any

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import httpx
import structlog
import tiktoken
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from airlock.config import AirlockConfig
from airlock.rate_limiter import CostTracker, TokenBucketRateLimiter
from airlock.scanner import OutputScanner, PIIScanner, PromptInjectionScanner

logger = structlog.get_logger()


def create_app(config: AirlockConfig) -> FastAPI:
    """Create the Airlock FastAPI application."""
    config = config.with_defaults()

    # Initialize components
    pii_scanner = PIIScanner(config.security.pii_rules)
    injection_scanner = PromptInjectionScanner(config.security.prompt_injection_rules)
    output_scanner = OutputScanner()
    rate_limiter = TokenBucketRateLimiter(
        requests_per_minute=config.rate_limit.requests_per_minute,
        tokens_per_minute=config.rate_limit.tokens_per_minute,
    )
    cost_tracker = CostTracker(budget_limit_usd=config.cost_tracking.budget_limit_usd)

    # Shared HTTP client for upstream calls — managed via lifespan
    http_client: httpx.AsyncClient | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        nonlocal http_client
        http_client = httpx.AsyncClient(
            base_url=config.upstream.base_url,
            timeout=config.upstream.timeout_seconds,
        )
        yield
        await http_client.aclose()

    app = FastAPI(
        title="Airlock",
        description="LLM Security Gateway",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/stats")
    async def stats() -> dict[str, Any]:
        return {
            "status": "running",
            "demo_mode": config.demo_mode,
            "security": {
                "pii_rules": len(config.security.pii_rules),
                "injection_rules": len(config.security.prompt_injection_rules),
            },
        }

    @app.api_route(
        "/v1/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    async def proxy(request: Request, path: str) -> Response:
        """Main proxy endpoint — intercepts all /v1/* requests."""
        start_time = time.monotonic()

        # Extract API key for rate limiting
        auth_header = request.headers.get("authorization", "")
        api_key = auth_header.replace("Bearer ", "")[:16] or "anonymous"

        log = logger.bind(
            path=path,
            method=request.method,
            client_key=api_key[:8] + "...",
        )

        # ── Step 1: Rate limiting ─────────────────────────────
        if config.rate_limit.enabled:
            rl_result = rate_limiter.check_request(api_key)
            if not rl_result.allowed:
                log.warning("rate_limit_exceeded", retry_after=rl_result.retry_after)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "message": "Rate limit exceeded",
                            "type": "rate_limit_error",
                            "retry_after": rl_result.retry_after,
                        }
                    },
                    headers={
                        "Retry-After": str(int(rl_result.retry_after or 1)),
                        "X-RateLimit-Remaining": str(rl_result.remaining),
                        "X-RateLimit-Limit": str(rl_result.limit),
                    },
                )

        # ── Step 2: Read request body ─────────────────────────
        body_bytes = await request.body()

        if request.method == "POST" and body_bytes:
            try:
                body = json.loads(body_bytes)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON body")
        else:
            body = None

        # ── Step 3: Scan request for security issues ──────────
        scan_log: dict[str, Any] = {}

        if body and isinstance(body, dict):
            messages = body.get("messages", [])
            full_prompt = " ".join(
                m.get("content", "") for m in messages if isinstance(m, dict)
            )

            # PII scan
            if config.security.pii_detection_enabled and full_prompt:
                pii_result = pii_scanner.scan(full_prompt, redact=True)
                if not pii_result.is_clean:
                    scan_log["pii_findings"] = len(pii_result.findings)
                    scan_log["pii_types"] = [
                        f.rule_name for f in pii_result.findings
                    ]
                    log.warning(
                        "pii_detected_in_request",
                        findings=len(pii_result.findings),
                        types=scan_log["pii_types"],
                    )
                    # Redact PII in the actual messages
                    if pii_result.redacted_text is not None:
                        body = _replace_message_content(
                            body, full_prompt, pii_result.redacted_text
                        )
                        body_bytes = json.dumps(body).encode()

            # Prompt injection scan
            if config.security.prompt_injection_enabled and full_prompt:
                injection_result = injection_scanner.scan(full_prompt)
                if not injection_result.is_clean:
                    scan_log["injection_findings"] = len(injection_result.findings)
                    scan_log["injection_rules"] = [
                        f.rule_name for f in injection_result.findings
                    ]
                    log.warning(
                        "prompt_injection_detected",
                        findings=len(injection_result.findings),
                        rules=scan_log["injection_rules"],
                    )
                    if injection_result.has_high_severity:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": {
                                    "message": "Request blocked: potential prompt injection detected",
                                    "type": "security_error",
                                    "findings": [
                                        {
                                            "rule": f.rule_name,
                                            "severity": f.severity.value,
                                        }
                                        for f in injection_result.findings
                                    ],
                                }
                            },
                        )

        # ── Step 4: Demo mode (return mock response) ──────────
        if config.demo_mode:
            mock_response = _demo_response(body, scan_log)
            log.info("demo_response", scan=scan_log)
            return JSONResponse(content=mock_response)

        # ── Step 5: Forward to upstream ───────────────────────
        headers = dict(request.headers)
        # Remove hop-by-hop headers
        for h in ["host", "transfer-encoding", "connection"]:
            headers.pop(h, None)

        if config.upstream.api_key:
            headers["authorization"] = f"Bearer {config.upstream.api_key}"

        assert http_client is not None, "HTTP client not initialized"
        try:
            upstream_response = await http_client.request(
                method=request.method,
                url=f"/v1/{path}",
                content=body_bytes,
                headers=headers,
            )
        except httpx.TimeoutException:
            log.error("upstream_timeout")
            return JSONResponse(
                status_code=504,
                content={"error": {"message": "Upstream timeout", "type": "timeout"}},
            )
        except httpx.ConnectError:
            log.error("upstream_connection_error")
            return JSONResponse(
                status_code=502,
                content={
                    "error": {
                        "message": "Cannot connect to upstream",
                        "type": "connection_error",
                    }
                },
            )

        # ── Step 6: Scan response ─────────────────────────────
        response_body = upstream_response.content
        response_data: dict[str, Any] | None = None

        try:
            response_data = json.loads(response_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        if config.security.scan_responses and response_data:
            response_text = _extract_response_text(response_data)
            if response_text:
                output_result = output_scanner.scan(response_text, pii_scanner)
                if not output_result.is_clean:
                    scan_log["response_findings"] = len(output_result.findings)
                    log.warning(
                        "response_scan_findings",
                        findings=len(output_result.findings),
                    )

        # ── Step 7: Cost tracking ─────────────────────────────
        if config.cost_tracking.enabled and response_data:
            usage = response_data.get("usage", {})
            model = response_data.get("model", body.get("model", "unknown") if body else "unknown")
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            if input_tokens or output_tokens:
                cost = cost_tracker.record(api_key, model, input_tokens, output_tokens)
                scan_log["cost_usd"] = round(cost.estimated_cost_usd, 6)
                scan_log["cumulative_cost_usd"] = round(cost.cumulative_cost_usd, 4)

                if cost.budget_exceeded:
                    log.warning(
                        "budget_exceeded",
                        cumulative=cost.cumulative_cost_usd,
                        limit=config.cost_tracking.budget_limit_usd,
                    )

                # Record token usage for rate limiting
                if config.rate_limit.enabled:
                    rate_limiter.record_token_usage(
                        api_key, input_tokens + output_tokens
                    )

        # ── Step 8: Log and return ────────────────────────────
        elapsed = time.monotonic() - start_time
        log.info(
            "request_completed",
            status=upstream_response.status_code,
            elapsed_ms=round(elapsed * 1000, 1),
            scan=scan_log,
        )

        return Response(
            content=response_body,
            status_code=upstream_response.status_code,
            headers={
                "content-type": upstream_response.headers.get(
                    "content-type", "application/json"
                ),
                "x-airlock-scan": json.dumps(scan_log) if scan_log else "clean",
            },
        )

    return app


def _replace_message_content(
    body: dict[str, Any], original: str, redacted: str
) -> dict[str, Any]:
    """Replace message content with redacted version."""
    if "messages" not in body:
        return body

    # Simple approach: rebuild content with redacted text
    # This works for the common case; production would need per-message redaction
    remaining = redacted
    for msg in body["messages"]:
        if isinstance(msg, dict) and "content" in msg:
            content = msg["content"]
            if isinstance(content, str) and content in original:
                # Find the corresponding portion of redacted text
                idx = original.find(content)
                if idx >= 0:
                    # Crude but functional: find same-length chunk in redacted
                    msg["content"] = remaining[: len(content)]
                    remaining = remaining[len(content) :]

    return body


def _extract_response_text(data: dict[str, Any]) -> str:
    """Extract text content from an OpenAI-format response."""
    texts: list[str] = []
    for choice in data.get("choices", []):
        msg = choice.get("message", {})
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if content:
                texts.append(content)
        # Also handle completion-style responses
        text = choice.get("text", "")
        if text:
            texts.append(text)
    return " ".join(texts)


def _demo_response(
    body: dict[str, Any] | None, scan_log: dict[str, Any]
) -> dict[str, Any]:
    """Generate a mock response for demo mode."""
    model = body.get("model", "demo-model") if body else "demo-model"
    return {
        "id": "airlock-demo-001",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        "[Airlock Demo] Your request was processed. "
                        f"Security scan: {json.dumps(scan_log) if scan_log else 'clean'}. "
                        "In production mode, this would forward to your LLM API."
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 25, "completion_tokens": 40, "total_tokens": 65},
        "_airlock": {
            "demo_mode": True,
            "scan": scan_log,
        },
    }
