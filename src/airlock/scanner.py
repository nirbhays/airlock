"""Security scanners — PII detection, prompt injection, and output scanning."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from airlock.config import PIIRule, PromptInjectionRule


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ScanFinding:
    """A single finding from a security scan."""

    rule_name: str
    category: str  # "pii", "injection", "output"
    severity: Severity
    matched_text: str
    start: int
    end: int
    message: str


@dataclass
class ScanResult:
    """Aggregated result of scanning a text."""

    findings: list[ScanFinding] = field(default_factory=list)
    redacted_text: str | None = None

    @property
    def is_clean(self) -> bool:
        return len(self.findings) == 0

    @property
    def has_high_severity(self) -> bool:
        return any(f.severity == Severity.HIGH for f in self.findings)

    def summary(self) -> dict[str, int]:
        """Count findings by category."""
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.category] = counts.get(f.category, 0) + 1
        return counts


class PIIScanner:
    """Detects and redacts PII from text using regex rules."""

    def __init__(self, rules: Sequence[PIIRule]) -> None:
        self._rules = [r for r in rules if r.enabled]
        self._compiled = [
            (r, re.compile(r.pattern)) for r in self._rules
        ]

    def scan(self, text: str, redact: bool = True) -> ScanResult:
        """Scan text for PII. If redact=True, also produce redacted version."""
        findings: list[ScanFinding] = []
        redacted = text

        for rule, pattern in self._compiled:
            for match in pattern.finditer(text):
                findings.append(
                    ScanFinding(
                        rule_name=rule.name,
                        category="pii",
                        severity=Severity.MEDIUM,
                        matched_text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        message=f"PII detected: {rule.name}",
                    )
                )
            if redact:
                redacted = pattern.sub(rule.replacement, redacted)

        return ScanResult(
            findings=findings,
            redacted_text=redacted if redact else None,
        )


class PromptInjectionScanner:
    """Detects prompt injection attempts using pattern matching."""

    def __init__(self, rules: Sequence[PromptInjectionRule]) -> None:
        self._rules = [r for r in rules if r.enabled]
        self._compiled = [
            (r, re.compile(r.pattern)) for r in self._rules
        ]

    def scan(self, text: str) -> ScanResult:
        """Scan text for prompt injection patterns."""
        findings: list[ScanFinding] = []

        for rule, pattern in self._compiled:
            for match in pattern.finditer(text):
                findings.append(
                    ScanFinding(
                        rule_name=rule.name,
                        category="injection",
                        severity=Severity(rule.severity),
                        matched_text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        message=f"Prompt injection detected: {rule.name}",
                    )
                )

        return ScanResult(findings=findings)


class OutputScanner:
    """Scans LLM responses for potentially harmful content."""

    # Patterns that might indicate the LLM is leaking system prompts
    LEAK_PATTERNS = [
        re.compile(r"(?i)my\s+(system\s+)?instructions\s+are"),
        re.compile(r"(?i)I\s+was\s+(told|instructed|programmed)\s+to"),
        re.compile(r"(?i)my\s+system\s+prompt\s+(is|says|reads)"),
    ]

    def scan(self, text: str, pii_scanner: PIIScanner | None = None) -> ScanResult:
        """Scan LLM output for concerning patterns and PII leakage."""
        findings: list[ScanFinding] = []

        # Check for system prompt leakage indicators
        for pattern in self.LEAK_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    ScanFinding(
                        rule_name="system_prompt_leak",
                        category="output",
                        severity=Severity.HIGH,
                        matched_text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        message="Potential system prompt leakage in response",
                    )
                )

        # Also scan output for PII if scanner provided
        pii_result: ScanResult | None = None
        if pii_scanner:
            pii_result = pii_scanner.scan(text, redact=True)
            findings.extend(pii_result.findings)

        return ScanResult(
            findings=findings,
            redacted_text=pii_result.redacted_text if pii_result else None,
        )
