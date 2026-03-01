# Airlock

**Drop-in LLM security proxy -- PII redaction, prompt injection defense, rate limiting, and cost tracking in one line.**

[![CI](https://github.com/YOUR_ORG/airlock/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/airlock/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/airlock-llm.svg)](https://pypi.org/project/airlock-llm/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Tests](https://img.shields.io/badge/tests-31%20passing-brightgreen)
![No External Services](https://img.shields.io/badge/runs-100%25%20local-orange)

> Point your `OPENAI_BASE_URL` at Airlock. Zero code changes. Full security pipeline.

---

## The Problem

You're sending user data to LLM APIs with no security layer:
- PII (emails, SSNs, credit cards) leaks to third-party APIs
- Prompt injection attacks go undetected
- No rate limiting = surprise bills
- No audit trail for compliance

## The Fix

```
Your App  →  Airlock  →  LLM API (OpenAI / Ollama / vLLM / etc.)
              │
              ├── PII Detection & Redaction
              ├── Prompt Injection Defense
              ├── Rate Limiting (request + token level)
              ├── Cost Tracking & Budget Alerts
              └── Structured Security Logging
```

## Quickstart

```bash
pip install -e .
airlock serve --demo
```

```bash
# In another terminal — send PII, watch it get caught
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"My SSN is 123-45-6789"}]}'
```

## Why Airlock?

| Problem | Without Airlock | With Airlock |
|---------|----------------|--------------|
| PII leaks to LLM APIs | Sensitive data sent in plaintext | Auto-detected and redacted before forwarding |
| Prompt injection | Unprotected | 6 pattern-based detectors, high-severity blocked |
| Cost overruns | No visibility until the bill | Per-key tracking, budget limits, token-level rate limiting |
| Audit compliance | Manual logging | Structured JSON logs with model, tokens, cost, scan results |
| Multiple tools needed | LiteLLM + guardrails + logging | Single proxy, one config file |

## CLI Reference

```
airlock serve [OPTIONS]     Start the security proxy
airlock check [OPTIONS]     Validate config and show active rules
airlock scan TEXT           Scan a string for PII and injection patterns
```

### `airlock serve`

| Flag | Default | Description |
|------|---------|-------------|
| `--config, -c` | — | Path to YAML config file |
| `--host, -h` | `0.0.0.0` | Bind host |
| `--port, -p` | `8080` | Bind port |
| `--demo` | off | Demo mode (mock responses, no upstream needed) |
| `--upstream-url` | `https://api.openai.com/v1` | Upstream LLM API URL |
| `--upstream-key` | — | API key for upstream |
| `--log-level` | `info` | `debug` / `info` / `warning` / `error` |

### Production Usage

```bash
# Proxy to OpenAI
airlock serve --upstream-key sk-your-key-here

# Proxy to local Ollama
airlock serve --upstream-url http://localhost:11434/v1

# With full config
airlock serve --config airlock.yaml
```

## Configuration

Copy `config.example.yaml` to `airlock.yaml`:

```yaml
security:
  pii_detection_enabled: true
  prompt_injection_enabled: true
  scan_responses: true

rate_limit:
  requests_per_minute: 60
  tokens_per_minute: 100000

cost_tracking:
  enabled: true
  budget_limit_usd: 50.0
```

### Custom PII Rules

```yaml
security:
  pii_rules:
    - name: "employee_id"
      pattern: "EMP-\\d{6}"
      replacement: "[EMPLOYEE_ID_REDACTED]"
```

## Security Features

**PII Detection & Redaction** — Built-in rules for email, phone, SSN, credit card, IP address. Extensible via config.

**Prompt Injection Defense** — Detects instruction override, system prompt extraction, role hijacking, DAN/jailbreak, delimiter injection, and encoding attacks. High-severity matches return `400`.

**Response Scanning** — Outbound responses scanned for PII leakage and system prompt disclosure.

## Architecture

```
Request → Rate Limit → PII Scan → Injection Scan → Proxy → Response Scan → Cost Track → Log
```

See [docs/architecture.md](docs/architecture.md) for C4 diagrams and extension points.

## Tradeoffs & Limitations

- **Pattern-based detection**: Uses regex, not ML models. Low latency but possible false negatives for novel attacks. Designed as a first layer of defense.
- **Single-process**: Rate limiting and cost tracking are in-memory. Redis integration planned for horizontal scaling.
- **No streaming yet**: Streaming responses are buffered before scanning.

## Roadmap

- [ ] Streaming response support
- [ ] Redis-backed rate limiting
- [ ] OpenTelemetry trace export
- [ ] ML-based prompt injection detection
- [ ] Plugin system for custom scanners
- [ ] Admin dashboard UI

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/ tests/
mypy src/
```

## License

MIT. See [LICENSE](LICENSE).
