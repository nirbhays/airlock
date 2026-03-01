# Changelog

All notable changes to Airlock will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-15

### Added

- FastAPI reverse proxy for OpenAI-compatible LLM APIs
- PII detection and redaction (email, phone, SSN, credit card, IP address)
- Prompt injection defense with 6 pattern categories
- Token bucket rate limiting (per-key, request + token level)
- Cost tracking with budget alerts and per-model pricing
- Response scanning for PII leakage
- Demo mode for testing without upstream API
- CLI commands: `serve`, `check`, `scan`
- YAML configuration support
- Structured JSON logging via structlog
