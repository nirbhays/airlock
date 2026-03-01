"""Token-bucket rate limiter for request and token-level throttling."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimitState:
    """Current state of a rate limiter bucket."""

    tokens: float
    last_refill: float
    total_requests: int = 0
    total_tokens_used: int = 0
    rejected_count: int = 0


class TokenBucketRateLimiter:
    """In-memory token bucket rate limiter.

    Supports both request-level and token-level rate limiting.
    Buckets are keyed by API key or IP address.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100_000,
    ) -> None:
        self._rpm = requests_per_minute
        self._tpm = tokens_per_minute
        self._request_buckets: dict[str, RateLimitState] = {}
        self._token_buckets: dict[str, RateLimitState] = {}
        self._lock = Lock()

    def check_request(self, key: str) -> RateLimitResult:
        """Check if a request is allowed under the rate limit."""
        with self._lock:
            now = time.monotonic()
            bucket = self._request_buckets.get(key)

            if bucket is None:
                bucket = RateLimitState(
                    tokens=float(self._rpm),
                    last_refill=now,
                )
                self._request_buckets[key] = bucket

            # Refill tokens based on elapsed time
            elapsed = now - bucket.last_refill
            bucket.tokens = min(
                float(self._rpm),
                bucket.tokens + elapsed * (self._rpm / 60.0),
            )
            bucket.last_refill = now

            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                bucket.total_requests += 1
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket.tokens),
                    limit=self._rpm,
                    retry_after=None,
                )
            else:
                bucket.rejected_count += 1
                retry_after = (1.0 - bucket.tokens) / (self._rpm / 60.0)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    limit=self._rpm,
                    retry_after=retry_after,
                )

    def record_token_usage(self, key: str, token_count: int) -> RateLimitResult:
        """Record token usage and check against token rate limit."""
        with self._lock:
            now = time.monotonic()
            bucket = self._token_buckets.get(key)

            if bucket is None:
                bucket = RateLimitState(
                    tokens=float(self._tpm),
                    last_refill=now,
                )
                self._token_buckets[key] = bucket

            # Refill
            elapsed = now - bucket.last_refill
            bucket.tokens = min(
                float(self._tpm),
                bucket.tokens + elapsed * (self._tpm / 60.0),
            )
            bucket.last_refill = now
            bucket.total_tokens_used += token_count

            if bucket.tokens >= token_count:
                bucket.tokens -= token_count
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket.tokens),
                    limit=self._tpm,
                    retry_after=None,
                )
            else:
                retry_after = (token_count - bucket.tokens) / (self._tpm / 60.0)
                return RateLimitResult(
                    allowed=False,
                    remaining=int(bucket.tokens),
                    limit=self._tpm,
                    retry_after=retry_after,
                )

    def get_stats(self, key: str) -> dict[str, int]:
        """Get usage statistics for a key."""
        req_bucket = self._request_buckets.get(key)
        tok_bucket = self._token_buckets.get(key)
        return {
            "total_requests": req_bucket.total_requests if req_bucket else 0,
            "total_tokens": tok_bucket.total_tokens_used if tok_bucket else 0,
            "rejected_requests": req_bucket.rejected_count if req_bucket else 0,
        }


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    limit: int
    retry_after: float | None = None


@dataclass
class CostTracker:
    """Tracks estimated API costs based on token usage."""

    # Approximate costs per 1K tokens (input/output) for common models
    MODEL_COSTS: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "gpt-4": (0.03, 0.06),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-3.5-turbo": (0.0005, 0.0015),
    })

    _usage: dict[str, dict[str, float]] = field(default_factory=dict)
    budget_limit_usd: float | None = None

    def record(
        self, key: str, model: str, input_tokens: int, output_tokens: int
    ) -> CostRecord:
        """Record token usage and calculate cost."""
        costs = self.MODEL_COSTS.get(model, (0.002, 0.002))  # fallback
        input_cost = (input_tokens / 1000) * costs[0]
        output_cost = (output_tokens / 1000) * costs[1]
        total_cost = input_cost + output_cost

        if key not in self._usage:
            self._usage[key] = {"total_cost": 0.0, "total_tokens": 0}

        self._usage[key]["total_cost"] += total_cost
        self._usage[key]["total_tokens"] += input_tokens + output_tokens

        budget_exceeded = False
        if self.budget_limit_usd is not None:
            budget_exceeded = self._usage[key]["total_cost"] > self.budget_limit_usd

        return CostRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=total_cost,
            cumulative_cost_usd=self._usage[key]["total_cost"],
            budget_exceeded=budget_exceeded,
        )

    def get_usage(self, key: str) -> dict[str, float]:
        """Get cumulative usage for a key."""
        return self._usage.get(key, {"total_cost": 0.0, "total_tokens": 0})


@dataclass
class CostRecord:
    """Record of cost for a single API call."""

    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    cumulative_cost_usd: float
    budget_exceeded: bool
