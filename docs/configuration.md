# Airlock Configuration Guide

## Configuration Sources

Airlock loads configuration from (in order of precedence):
1. CLI flags (highest)
2. Environment variables (`AIRLOCK_` prefix)
3. YAML config file
4. Defaults (lowest)

## YAML Configuration

Copy the example and customize:

```bash
cp config.example.yaml airlock.yaml
airlock serve --config airlock.yaml
```

### Full Reference

```yaml
# Server
host: "0.0.0.0"
port: 8080
log_level: "info"           # debug, info, warning, error
demo_mode: false

# Upstream LLM API
upstream:
  base_url: "https://api.openai.com/v1"
  api_key: ""               # Prefer env: AIRLOCK_UPSTREAM__API_KEY
  timeout_seconds: 30.0
  max_retries: 2

# Security
security:
  pii_detection_enabled: true
  prompt_injection_enabled: true
  scan_responses: true

  pii_rules:                # Extends (does not replace) built-in rules
    - name: "employee_id"
      pattern: "EMP-\\d{6}"
      replacement: "[EMPLOYEE_ID_REDACTED]"
      enabled: true

  prompt_injection_rules:   # Extends built-in rules
    - name: "custom_block"
      pattern: "(?i)override\\s+safety"
      severity: "high"
      enabled: true

# Rate Limiting
rate_limit:
  enabled: true
  requests_per_minute: 60
  tokens_per_minute: 100000

# Cost Tracking
cost_tracking:
  enabled: true
  budget_limit_usd: null    # Set to a number to enable budget alerts
  log_usage: true
```

## Environment Variables

All config values can be set via environment variables with `AIRLOCK_` prefix and `__` for nesting:

```bash
export AIRLOCK_PORT=9090
export AIRLOCK_UPSTREAM__API_KEY=sk-your-key
export AIRLOCK_UPSTREAM__BASE_URL=http://localhost:11434/v1
export AIRLOCK_LOG_LEVEL=debug
export AIRLOCK_DEMO_MODE=true
```

## Custom PII Rules

Each PII rule has:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier for the rule |
| `pattern` | string | Python regex pattern |
| `replacement` | string | Text to replace matches with |
| `enabled` | bool | Whether the rule is active |

The pattern is compiled as a Python `re` regex. Use raw string escaping for backslashes in YAML.

### Built-in Rules

| Name | Detects | Replacement |
|------|---------|-------------|
| `email` | Email addresses | `[EMAIL_REDACTED]` |
| `phone_us` | US phone numbers | `[PHONE_REDACTED]` |
| `ssn` | Social Security Numbers | `[SSN_REDACTED]` |
| `credit_card` | Credit card numbers | `[CC_REDACTED]` |
| `ip_address` | IPv4 addresses | `[IP_REDACTED]` |

## Custom Injection Rules

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier |
| `pattern` | string | Python regex pattern |
| `severity` | string | `low`, `medium`, `high` |
| `enabled` | bool | Whether active |

**High severity** rules cause the request to be blocked (HTTP 400). Medium and low are logged only.

## Validating Configuration

```bash
airlock check --config airlock.yaml
```

This shows all active rules and their status without starting the server.
