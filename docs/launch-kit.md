# Airlock Launch Kit

## HN Post Draft

**Title:** Show HN: Airlock – Open-source LLM security proxy with PII redaction and prompt injection defense

**Body:**
Hi HN, I built Airlock, an open-source reverse proxy that sits between your app and any OpenAI-compatible LLM API. It adds:

- PII detection and redaction (email, SSN, credit cards, custom patterns)
- Prompt injection defense (6+ pattern detectors, blocks high-severity attempts)
- Per-key rate limiting (request + token level)
- Cost tracking with budget alerts
- Structured JSON audit logs for every request

It's a single Python process, configured via YAML, and works with OpenAI, Ollama, vLLM, or any OpenAI-compatible endpoint. No code changes needed — just point your OPENAI_BASE_URL at Airlock.

Demo in 30 seconds:
```
pip install airlock-llm
airlock serve --demo
curl localhost:8080/v1/chat/completions -d '{"model":"gpt-4","messages":[{"role":"user","content":"My SSN is 123-45-6789"}]}'
```

GitHub: [link]

I built this because every team I've worked with has the same problem: sensitive data leaking to LLM APIs, no visibility into costs, and prompt injection is an afterthought. Existing tools are either Python-only guardrails (slow), cost managers (no security), or enterprise products (expensive). Airlock unifies these into one proxy.

Feedback welcome, especially on the detection rules and what you'd want to see next.

---

## Reddit Post Draft (r/MachineLearning or r/LocalLLaMA)

**Title:** I built an open-source LLM security proxy — detects PII, blocks prompt injections, tracks costs

Tired of worrying about sensitive data leaking to LLM APIs? I built Airlock, a drop-in reverse proxy that scans every request and response for PII, prompt injection attempts, and cost overruns.

Works with OpenAI, Ollama, vLLM — anything OpenAI-compatible. Zero code changes: just change your base URL.

**Features:**
- PII redaction (email, SSN, CC, custom regex)
- Prompt injection detection and blocking
- Rate limiting + cost tracking
- Structured audit logs

**Demo:** `pip install airlock-llm && airlock serve --demo`

MIT licensed. Looking for feedback and contributors.

---

## LinkedIn Post Draft

🔒 Just open-sourced Airlock — an LLM security gateway for teams using AI in production.

Every organization using LLM APIs faces the same challenges:
→ Sensitive data (PII) leaking in prompts
→ No defense against prompt injection
→ Cost overruns with no per-team visibility
→ Compliance teams asking for audit logs

Airlock is a drop-in reverse proxy that solves all four. No code changes — configure it once, and every LLM request is scanned, rate-limited, cost-tracked, and logged.

Built for teams that need security without slowing down development.

Open source (MIT): [GitHub link]

#LLM #AISecurity #OpenSource #MLOps

---

## 10 Build-in-Public Update Titles

1. "Day 1: Shipped v0.1 of Airlock — PII redaction works, but I found 3 edge cases in SSN detection"
2. "How I designed a prompt injection detector using only regex (and why ML is overkill for 80% of cases)"
3. "Airlock cost tracking saved a team $200 in one day — here's how budget alerts work"
4. "The hardest part of building an LLM proxy: handling streaming responses while scanning for PII"
5. "Added custom PII rules to Airlock — one user is detecting medical record numbers"
6. "100 stars in week 1: what worked and what I'd do differently"
7. "Why I chose Python over Go for an LLM proxy (and when I'd switch)"
8. "Airlock v0.2: Token-level rate limiting is live — here's the algorithm"
9. "Building a security tool that people actually want to use: UX lessons from Airlock"
10. "Airlock + Ollama: How to secure your local LLM deployment in 5 minutes"

---

## Benchmark Plan

**Chart: "Request latency overhead of Airlock proxy"**

Setup:
1. Direct requests to Ollama (baseline)
2. Requests through Airlock with all scanning enabled
3. Requests through Airlock with only PII scanning
4. Requests through Airlock with only rate limiting

Measure: p50, p95, p99 latency for 1000 sequential requests.

Expected result: <5ms overhead for regex-based scanning.

Tool: `hyperfine` or custom Python script with `httpx` timing.

Output: Bar chart comparing latency percentiles, shareable as PNG.

---

## Before vs After Story

**Before:** Screenshot of a curl request to OpenAI with PII in the prompt (email, SSN visible in plaintext). Server logs show nothing.

**After:** Same curl request through Airlock. Response shows PII was redacted. Server logs show structured JSON with scan findings, cost tracking, and redacted content. Terminal output with color-coded security findings.

---

## 30-Day Roadmap

| Week | Milestone |
|------|-----------|
| Week 1 | v0.1.0 release. HN + Reddit launch. Collect feedback. |
| Week 2 | Fix top 3 reported issues. Add streaming passthrough mode. |
| Week 3 | v0.2.0: Redis-backed rate limiting. Docker image. |
| Week 4 | v0.3.0: OpenTelemetry trace export. Benchmark blog post. |

---

## 20 Good First Issues

1. Add IP address v6 detection rule
2. Add Australian phone number PII rule
3. Add UK National Insurance Number PII rule
4. Add German IBAN detection rule
5. Add configurable response for blocked requests (custom error message)
6. Add `/metrics` endpoint with request count and scan statistics
7. Add `--json` flag to `airlock scan` for machine-readable output
8. Add Docker Compose example with Ollama
9. Add request body size limit configuration
10. Add PII detection for dates of birth (common formats)
11. Write tutorial: "Using Airlock with LangChain"
12. Add cost tracking for Anthropic Claude models
13. Add cost tracking for open-source models (Llama, Mistral)
14. Add `airlock test-rules` command to test custom rules against sample inputs
15. Add CORS configuration options
16. Add request/response logging to file (in addition to stdout)
17. Add support for multiple upstream endpoints (load balancing)
18. Add regex validation on config load (fail fast on invalid patterns)
19. Write tutorial: "Using Airlock with Ollama"
20. Add GitHub Actions workflow template for running Airlock in CI
