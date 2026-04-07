# Airlock Roadmap

## Vision
Every LLM API call should pass through a security layer by default — zero config, zero trust.

## ✅ Shipped
- PII detection and redaction (emails, SSNs, credit cards, phone numbers)
- 6 prompt injection detectors
- Rate limiting per client
- Cost budget enforcement
- 31+ tests
- 100% local — no data leaves your infrastructure

## 🔨 In Progress
- [ ] Streaming response support (SSE)
- [ ] Custom PII regex patterns
- [ ] Ollama provider support

## 📋 Planned — Q2 2025
- [ ] Redis-backed distributed rate limiting
- [ ] OpenTelemetry trace export
- [ ] Admin dashboard UI
- [ ] Audit log export (JSONL / S3)

## 📋 Planned — Q3 2025
- [ ] ML-based prompt injection detection (beyond regex)
- [ ] Plugin system for custom scanners
- [ ] Kubernetes sidecar deployment mode
- [ ] SOC 2 compliance report generation from audit logs

## 💡 Under Consideration
- Anthropic + Google provider native support
- WASM build for edge deployment
- Cloudflare Workers compatibility

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). The streaming support issue is a great first contribution.
