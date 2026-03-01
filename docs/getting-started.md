# Getting Started with Airlock

## Prerequisites

- Python 3.10 or later
- pip

## Installation

```bash
pip install -e .

# Verify
airlock --version
```

## Your First Run (Demo Mode)

Demo mode runs Airlock without requiring any LLM API credentials. It returns mock responses while fully exercising the security pipeline.

```bash
airlock serve --demo
```

You should see:

```
  Airlock is running in DEMO MODE
  Listening on http://0.0.0.0:8080
  Send requests to /v1/chat/completions to see security scanning.
```

### Send a Test Request

In another terminal:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My email is test@example.com"}]
  }'
```

Check the server logs — you'll see the PII detection in the structured output.

## Connecting to a Real LLM API

### OpenAI

```bash
airlock serve --upstream-key sk-your-key-here
```

### Ollama (local)

```bash
# Start Ollama first
ollama serve

# Point Airlock at it
airlock serve --upstream-url http://localhost:11434/v1
```

### Any OpenAI-compatible API

```bash
airlock serve --upstream-url http://your-api:8000/v1 --upstream-key your-key
```

## Using from Your Application

Point your OpenAI client at Airlock instead of the upstream API:

```python
from openai import OpenAI

# Before: client = OpenAI()
# After:
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="your-real-api-key",  # Airlock forwards this
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

## Configuration File

For production use, create a config file:

```bash
cp config.example.yaml airlock.yaml
# Edit airlock.yaml with your settings
airlock serve --config airlock.yaml
```

## CLI Quick Reference

```bash
airlock serve --demo              # Demo mode
airlock serve --config FILE       # Production mode with config
airlock check                     # Validate configuration
airlock check --config FILE       # Validate specific config
airlock scan "some text"          # Scan text for PII/injection
```

## Next Steps

- [Configuration Guide](configuration.md)
- [Architecture](architecture.md)
- [Security Details](security.md)
