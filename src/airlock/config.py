"""Configuration models for Airlock."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PIIRule(BaseModel):
    """A single PII detection rule."""

    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    enabled: bool = True


class PromptInjectionRule(BaseModel):
    """A prompt injection detection pattern."""

    name: str
    pattern: str
    severity: str = "high"  # low, medium, high
    enabled: bool = True


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    tokens_per_minute: int = 100_000
    enabled: bool = True


class CostTrackingConfig(BaseModel):
    """Cost tracking configuration."""

    enabled: bool = True
    budget_limit_usd: float | None = None
    log_usage: bool = True


class SecurityConfig(BaseModel):
    """Security scanning configuration."""

    pii_detection_enabled: bool = True
    pii_rules: list[PIIRule] = Field(default_factory=list)
    prompt_injection_enabled: bool = True
    prompt_injection_rules: list[PromptInjectionRule] = Field(default_factory=list)
    scan_responses: bool = True


class UpstreamConfig(BaseModel):
    """Upstream LLM API configuration."""

    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    timeout_seconds: float = 30.0
    max_retries: int = 2


class AirlockConfig(BaseSettings):
    """Root configuration for Airlock gateway."""

    host: str = "0.0.0.0"
    port: int = 8080
    upstream: UpstreamConfig = Field(default_factory=UpstreamConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cost_tracking: CostTrackingConfig = Field(default_factory=CostTrackingConfig)
    log_level: str = "info"
    demo_mode: bool = False

    @classmethod
    def from_yaml(cls, path: Path) -> AirlockConfig:
        """Load configuration from a YAML file."""
        with open(path) as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
        return cls(**data)

    def with_defaults(self) -> AirlockConfig:
        """Apply default PII and injection rules if none configured."""
        if not self.security.pii_rules:
            self.security.pii_rules = _default_pii_rules()
        if not self.security.prompt_injection_rules:
            self.security.prompt_injection_rules = _default_injection_rules()
        return self


def _default_pii_rules() -> list[PIIRule]:
    """Built-in PII detection rules."""
    return [
        PIIRule(
            name="email",
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            replacement="[EMAIL_REDACTED]",
        ),
        PIIRule(
            name="phone_us",
            pattern=r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            replacement="[PHONE_REDACTED]",
        ),
        PIIRule(
            name="ssn",
            pattern=r"\b\d{3}-\d{2}-\d{4}\b",
            replacement="[SSN_REDACTED]",
        ),
        PIIRule(
            name="credit_card",
            pattern=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            replacement="[CC_REDACTED]",
        ),
        PIIRule(
            name="ip_address",
            pattern=r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            replacement="[IP_REDACTED]",
        ),
    ]


def _default_injection_rules() -> list[PromptInjectionRule]:
    """Built-in prompt injection detection patterns."""
    return [
        PromptInjectionRule(
            name="ignore_instructions",
            pattern=r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)",
            severity="high",
        ),
        PromptInjectionRule(
            name="system_prompt_leak",
            pattern=r"(?i)(reveal|show|print|output|display|repeat)\s+(your|the|system)\s+(system\s+)?(prompt|instructions|rules)",
            severity="high",
        ),
        PromptInjectionRule(
            name="role_override",
            pattern=r"(?i)you\s+are\s+now\s+(a|an|the|DAN|evil|unrestricted)",
            severity="high",
        ),
        PromptInjectionRule(
            name="jailbreak_dan",
            pattern=r"(?i)(DAN|do\s+anything\s+now|jailbreak|bypass\s+filters)",
            severity="high",
        ),
        PromptInjectionRule(
            name="delimiter_injection",
            pattern=r"(?i)(```|<\|im_sep\|>|<\|im_start\|>|<\|endoftext\|>|\[INST\])",
            severity="medium",
        ),
        PromptInjectionRule(
            name="encoding_attack",
            pattern=r"(?i)(base64|rot13|hex|encode|decode)\s+(the\s+following|this)",
            severity="medium",
        ),
    ]
