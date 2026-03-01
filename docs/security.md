# Airlock Security Documentation

## Threat Model

Airlock protects against threats in the OWASP Top 10 for LLMs:

| OWASP LLM Risk | Airlock Mitigation | Status |
|----------------|-------------------|--------|
| LLM01: Prompt Injection | Pattern-based detection, request blocking | v0.1 |
| LLM02: Insecure Output | Response scanning for leaks | v0.1 |
| LLM04: DoS | Request + token rate limiting | v0.1 |
| LLM05: Insecure Code Output | — | Roadmap |
| LLM06: PII Disclosure | PII detection + redaction | v0.1 |
| LLM08: Agent Misalignment | — | Roadmap |
| LLM10: Unbounded Consumption | Budget limits, cost tracking | v0.1 |

## PII Detection Rules

Built-in rules detect:
- Email addresses
- US phone numbers
- US Social Security Numbers
- Credit card numbers (Luhn-valid patterns)
- IP addresses

Custom rules can be added via YAML configuration using any valid Python regex.

### Limitations

- Regex-based: will miss PII in unusual formats or non-English contexts
- No Named Entity Recognition (NER) — planned for future versions
- Credit card detection uses format matching, not Luhn validation

## Prompt Injection Detection

Built-in detectors:
- Instruction override attempts ("ignore previous instructions")
- System prompt extraction attempts
- Role hijacking (DAN, unrestricted mode)
- Jailbreak keywords
- Delimiter injection (special tokens)
- Encoding-based attacks (base64, rot13)

### Response

- **High severity**: Request is blocked with HTTP 400
- **Medium severity**: Request is logged and forwarded (configurable)
- **Low severity**: Logged only

## Rate Limiting

- Token bucket algorithm, per API key
- Dual limits: requests/minute and tokens/minute
- In-memory state (not shared across processes)

## Cost Tracking

- Estimates cost based on model and token counts
- Configurable budget limit per API key
- Logs cumulative spend

## Logging & Audit

All requests produce structured JSON log entries containing:
- Timestamp
- Client identifier (truncated API key)
- Request path and method
- Scan findings (categories and counts, not PII content)
- Response status
- Token usage and estimated cost
- Request duration

PII content is **never logged** — only the rule name and detection count.

## Deployment Security

- Run Airlock as an unprivileged user
- Use TLS termination in front of Airlock (nginx, cloud LB)
- Set `upstream.api_key` via environment variable, not config file
- Restrict network access to the Airlock port
