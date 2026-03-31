# CLAUDE.md — Airlock

Airlock is a drop-in LLM security proxy written in Python. It intercepts every
request/response between your application and any OpenAI-compatible LLM API,
applying a sequential pipeline of security scans, rate limiting, and cost
tracking — with zero code changes to the calling application.

## Project Owner

Nirbhay Singh — Cloud and AI Architect based in Warsaw. Airlock is part of
his AI security portfolio, which also includes:
- shieldiac — IaC (Terraform/CloudFormation) security scanner
- tokenmeter — standalone LLM cost tracking and budget alerting

## Repo Layout

```
src/airlock/
  __init__.py      version string
  cli.py           Click CLI: serve / check / scan subcommands
  proxy.py         FastAPI app — the 8-step request/response pipeline
  scanner.py       PIIScanner, PromptInjectionScanner, OutputScanner
  rate_limiter.py  TokenBucketRateLimiter + CostTracker
  config.py        Pydantic/pydantic-settings models + default rule sets
tests/
  test_scanner.py       scanner unit tests
  test_rate_limiter.py  rate limiter + cost tracker tests
  test_integration.py   end-to-end proxy tests (demo mode)
docs/
  architecture.md   C4 diagrams, design decisions, extension points
  configuration.md  full config reference
  getting-started.md quickstart walkthrough
config.example.yaml  annotated YAML config template
```

## How the Proxy Works

The entry point is `create_app(config)` in `proxy.py`, which returns a FastAPI
app. Every request to `/v1/{path:path}` goes through eight sequential steps
(all synchronous in the request path — no unscanned traffic ever reaches
the upstream LLM):

```
Step 1  Rate limit check    — returns 429 if bucket exhausted
Step 2  Read request body   — JSON-decoded into a dict
Step 3  PII scan            — regex over concatenated message content; redact and log
Step 4  Injection scan      — regex; high-severity findings return 400 blocked
Step 5  Demo mode short-circuit (if --demo flag is active)
Step 6  Forward to upstream — httpx async client (lifespan-managed)
Step 7  Response scan       — PII + system-prompt-leak patterns on LLM output
Step 8  Cost tracking       — token usage recorded; budget alert if exceeded
        Structured JSON log + X-Airlock-Scan response header returned to client
```

The FastAPI app is served by uvicorn. The lifespan context manager creates and
closes a single shared `httpx.AsyncClient` for all upstream calls, enabling
connection reuse and proper cleanup.

## PII Detection and Redaction

Location: `src/airlock/scanner.py` — class `PIIScanner`
Default rules: `src/airlock/config.py` — function `_default_pii_rules()`

Built-in rules (regex patterns, all enabled by default):

| Rule name    | Pattern matches           | Replacement token     |
|--------------|---------------------------|-----------------------|
| email        | user@domain.tld           | [EMAIL_REDACTED]      |
| phone_us     | NXX-NXX-XXXX              | [PHONE_REDACTED]      |
| ssn          | NNN-NN-NNNN               | [SSN_REDACTED]        |
| credit_card  | 16-digit grouped numbers  | [CC_REDACTED]         |
| ip_address   | N.N.N.N                   | [IP_REDACTED]         |

`PIIScanner.scan(text, redact=True)` iterates compiled regex patterns, collects
`ScanFinding` objects (rule_name, start, end, matched_text, severity=MEDIUM),
and simultaneously builds a redacted copy of the text via `re.sub`. The redacted
text replaces message content in the body forwarded to upstream.

`OutputScanner.scan(text, pii_scanner)` checks LLM *responses* for PII leakage,
plus three additional regex patterns that detect system-prompt disclosure:
"my instructions are…", "I was instructed to…", "my system prompt says…".

## Prompt Injection Defense

Location: `src/airlock/scanner.py` — class `PromptInjectionScanner`
Default rules: `src/airlock/config.py` — function `_default_injection_rules()`

Six built-in rules, each with a compiled regex and a severity level:

| Rule name             | Severity | Detects                                       |
|-----------------------|----------|-----------------------------------------------|
| ignore_instructions   | high     | "ignore all previous instructions"            |
| system_prompt_leak    | high     | "reveal your system prompt"                   |
| role_override         | high     | "you are now an unrestricted AI"              |
| jailbreak_dan         | high     | DAN, do anything now, bypass filters          |
| delimiter_injection   | medium   | backtick fences, im_sep tokens, [INST]        |
| encoding_attack       | medium   | "base64 decode the following"                 |

`PromptInjectionScanner.scan(text)` returns a `ScanResult`. If
`result.has_high_severity` is True, the proxy returns HTTP 400 with a JSON
body listing rule names and severities — the request never reaches the LLM.

Medium-severity findings are logged but not blocked; they appear in the
structured log and the X-Airlock-Scan response header.

## Rate Limiting

Location: `src/airlock/rate_limiter.py` — class `TokenBucketRateLimiter`

Uses an in-memory token bucket per API key (extracted from the Authorization
header, first 16 chars). Two independent buckets per key:

1. Request bucket: refills at `requests_per_minute / 60` tokens per second.
   `check_request(key)` is called at Step 1. Returns 429 with Retry-After
   and X-RateLimit-* headers when the bucket is empty.
2. Token bucket: `record_token_usage(key, token_count)` is called after a
   successful upstream response. Monitored but not blocking in v0.1.

State is protected by a `threading.Lock`. Buckets are per-process in-memory;
Redis-backed distributed rate limiting is on the roadmap.

## Cost Tracking

Location: `src/airlock/rate_limiter.py` — dataclass `CostTracker`

`CostTracker.record(key, model, input_tokens, output_tokens)` multiplies token
counts against a hard-coded per-1K cost table for common OpenAI models
(gpt-4, gpt-4o, gpt-4o-mini, gpt-3.5-turbo) and accumulates totals per API
key in an in-memory dict. Returns a `CostRecord` with `budget_exceeded=True`
when the cumulative cost exceeds `budget_limit_usd`. A structlog warning is
emitted; requests are not yet blocked on budget (roadmap item).

## Configuration System

Location: `src/airlock/config.py` — `AirlockConfig` (pydantic-settings class)

Load order: YAML file via `AirlockConfig.from_yaml(path)`, then CLI overrides.
`config.with_defaults()` is called at startup to inject built-in PII and
injection rule sets when none are present in the YAML.

Key nested models:
- `SecurityConfig`: pii_rules list, prompt_injection_rules list, scan_responses flag
- `RateLimitConfig`: requests_per_minute, tokens_per_minute, enabled flag
- `CostTrackingConfig`: enabled, budget_limit_usd, log_usage
- `UpstreamConfig`: base_url, api_key, timeout_seconds, max_retries

## Installation and Running

```bash
# Install for development (editable with dev extras)
pip install -e ".[dev]"

# Demo mode: no upstream LLM needed, returns mock responses
airlock serve --demo

# Proxy to OpenAI
airlock serve --upstream-key sk-your-key

# Proxy to local Ollama
airlock serve --upstream-url http://localhost:11434/v1

# With a YAML config file
airlock serve --config airlock.yaml

# Validate config and list all active rules (no server started)
airlock check --config airlock.yaml

# Scan a string from the command line
airlock scan "My SSN is 123-45-6789 and email is foo@example.com"
```

PyPI package name: `airlock-llm` (`pip install airlock-llm`).
Default listen address: `http://0.0.0.0:8080`.
Health check: `GET /health` returns `{"status": "healthy", "version": "0.1.0"}`.
Stats: `GET /stats` returns rule counts and demo_mode flag.

## Using as a Drop-In Proxy

Any application that supports OPENAI_BASE_URL works without code changes:

```bash
export OPENAI_BASE_URL=http://localhost:8080/v1
export OPENAI_API_KEY=sk-your-key   # forwarded as-is to upstream
```

This covers the OpenAI Python SDK, LangChain, LlamaIndex, llm CLI, and any
other OpenAI-compatible client.

## Testing

```bash
pip install -e ".[dev]"
pytest                        # run all 31 tests
pytest tests/test_scanner.py  # scanner unit tests only
pytest -v --tb=short          # verbose output with short tracebacks
pytest --cov=airlock --cov-report=term-missing  # with coverage
```

Test files:
- `tests/test_scanner.py` — PIIScanner, PromptInjectionScanner, OutputScanner
- `tests/test_rate_limiter.py` — TokenBucketRateLimiter and CostTracker
- `tests/test_integration.py` — full pipeline via httpx TestClient in demo mode

No external services required. All integration tests run in demo mode
(mock responses, no upstream LLM calls).

## How to Add a New Security Rule

### Option A: YAML config (no code change)

```yaml
# airlock.yaml
security:
  pii_rules:
    - name: "employee_id"
      pattern: "EMP-\\d{6}"
      replacement: "[EMPLOYEE_ID_REDACTED]"
      enabled: true
  prompt_injection_rules:
    - name: "competitor_override"
      pattern: "(?i)you\\s+are\\s+now\\s+GPT-5"
      severity: "high"
      enabled: true
```

Restart the server (or run `airlock check`) to validate the new rule. The
regex is compiled at startup — an invalid pattern raises an error immediately.

### Option B: Built-in code rules

1. Open `src/airlock/config.py`.
2. Add a `PIIRule(...)` entry to `_default_pii_rules()`, or a
   `PromptInjectionRule(...)` entry to `_default_injection_rules()`.
3. Test the pattern: `airlock scan "your test string"`
4. Add a test in `tests/test_scanner.py`.

### Option C: Custom output scanner

Subclass `OutputScanner` in `scanner.py` and extend the `LEAK_PATTERNS` list,
or override the `scan()` method entirely. Update `create_app()` in `proxy.py`
to instantiate your subclass instead of the default.

## Code Style and Tooling

```bash
ruff check src/ tests/    # linting (line-length 88)
ruff format src/ tests/   # auto-formatting
mypy src/                 # strict type checking
```

Python 3.10+ is required. The codebase uses structural pattern matching
(match/case) in some places. All public APIs have docstrings. Pydantic v2 is
required; v1 is not supported.

## Key Dependencies

| Package           | Role                                         |
|-------------------|----------------------------------------------|
| fastapi           | HTTP framework for the proxy server          |
| uvicorn[standard] | ASGI server                                  |
| httpx             | Async HTTP client for upstream calls         |
| pydantic v2       | Config models and data validation            |
| pydantic-settings | Environment variable config loading          |
| tiktoken          | Token counting for cost tracking             |
| structlog         | Structured JSON logging                      |
| click             | CLI framework                                |
| pyyaml            | YAML config loading                          |
| rich              | Terminal output formatting                   |

## Architecture and Failure Modes

The scanning pipeline is synchronous in the hot path — regex scans add
approximately 1-2ms per request, ensuring no unscanned traffic reaches
upstream. Full C4 container/component diagrams and a Mermaid sequence diagram
live in `docs/architecture.md`.

Failure modes:
- Upstream timeout: returns 504 (configurable via `UpstreamConfig.timeout_seconds`)
- Upstream unreachable: returns 502
- Config parse error: fails at startup with a descriptive message
- Invalid regex in a rule: compile-time error at startup (caught by `airlock check`)
- OOM from large request: no size limit yet (roadmap item)

## Roadmap

- Streaming response support (passthrough mode without response scanning)
- Redis-backed distributed rate limiting for multi-instance deployments
- OpenTelemetry trace export
- ML-based prompt injection detection as an optional plugin
- Admin dashboard UI
- Request size limits to prevent out-of-memory crashes
