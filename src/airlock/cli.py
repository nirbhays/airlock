"""Airlock CLI — the main entry point."""

from __future__ import annotations

from pathlib import Path

import click
import structlog
import uvicorn

from airlock import __version__
from airlock.config import AirlockConfig


def _setup_logging(level: str) -> None:
    """Configure structlog for structured JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if level == "debug"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(level)
        ),
    )


@click.group()
@click.version_option(version=__version__, prog_name="airlock")
def main() -> None:
    """Airlock — LLM Security Gateway.

    Drop-in reverse proxy that adds PII redaction, prompt injection defense,
    rate limiting, and cost tracking to any OpenAI-compatible LLM API.
    """


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to YAML config file.",
)
@click.option("--host", "-h", default="0.0.0.0", help="Bind host.")
@click.option("--port", "-p", default=8080, type=int, help="Bind port.")
@click.option("--demo", is_flag=True, help="Run in demo mode (no upstream required).")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="Log level.",
)
@click.option(
    "--upstream-url",
    default=None,
    help="Upstream LLM API base URL (e.g., http://localhost:11434/v1 for Ollama).",
)
@click.option(
    "--upstream-key",
    default=None,
    help="API key for upstream LLM API.",
)
def serve(
    config: Path | None,
    host: str,
    port: int,
    demo: bool,
    log_level: str,
    upstream_url: str | None,
    upstream_key: str | None,
) -> None:
    """Start the Airlock security proxy.

    \b
    Examples:
      # Demo mode (no API key needed)
      airlock serve --demo

      # Proxy to OpenAI
      airlock serve --upstream-key sk-...

      # Proxy to local Ollama
      airlock serve --upstream-url http://localhost:11434/v1

      # With config file
      airlock serve --config airlock.yaml
    """
    if config:
        cfg = AirlockConfig.from_yaml(config)
    else:
        cfg = AirlockConfig()

    # CLI overrides
    cfg.host = host
    cfg.port = port
    cfg.log_level = log_level

    if demo:
        cfg.demo_mode = True

    if upstream_url:
        cfg.upstream.base_url = upstream_url

    if upstream_key:
        cfg.upstream.api_key = upstream_key

    _setup_logging(cfg.log_level)
    log = structlog.get_logger()

    log.info(
        "starting_airlock",
        host=cfg.host,
        port=cfg.port,
        demo_mode=cfg.demo_mode,
        upstream=cfg.upstream.base_url if not cfg.demo_mode else "disabled",
        pii_rules=len(cfg.with_defaults().security.pii_rules),
        injection_rules=len(cfg.with_defaults().security.prompt_injection_rules),
    )

    if cfg.demo_mode:
        click.echo(
            click.style("\n  Airlock", fg="cyan", bold=True)
            + " is running in "
            + click.style("DEMO MODE", fg="yellow", bold=True)
        )
        click.echo(f"  Listening on http://{cfg.host}:{cfg.port}")
        click.echo(
            "  Send requests to /v1/chat/completions to see security scanning.\n"
        )
        click.echo("  Try it:")
        click.echo(
            click.style(
                f'  curl http://localhost:{cfg.port}/v1/chat/completions \\\n'
                f'    -H "Content-Type: application/json" \\\n'
                f'    -d \'{{"model": "gpt-4", "messages": [{{"role": "user", "content": '
                f'"My email is john@example.com and my SSN is 123-45-6789"}}]}}\'\n',
                fg="green",
            )
        )

    from airlock.proxy import create_app

    app = create_app(cfg)
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level=cfg.log_level)


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to YAML config file.",
)
def check(config: Path | None) -> None:
    """Validate configuration and show active rules.

    \b
    Examples:
      airlock check
      airlock check --config airlock.yaml
    """
    if config:
        cfg = AirlockConfig.from_yaml(config)
    else:
        cfg = AirlockConfig()

    cfg = cfg.with_defaults()

    click.echo(click.style("Airlock Configuration Check", fg="cyan", bold=True))
    click.echo()
    click.echo(f"  Upstream: {cfg.upstream.base_url}")
    click.echo(f"  Demo mode: {cfg.demo_mode}")
    click.echo()
    click.echo(click.style("  Security Rules:", bold=True))
    click.echo(f"    PII detection: {cfg.security.pii_detection_enabled}")
    click.echo(f"    PII rules: {len(cfg.security.pii_rules)}")
    for rule in cfg.security.pii_rules:
        status = click.style("ON", fg="green") if rule.enabled else click.style("OFF", fg="red")
        click.echo(f"      [{status}] {rule.name}: {rule.replacement}")

    click.echo(f"    Injection detection: {cfg.security.prompt_injection_enabled}")
    click.echo(f"    Injection rules: {len(cfg.security.prompt_injection_rules)}")
    for rule in cfg.security.prompt_injection_rules:
        status = click.style("ON", fg="green") if rule.enabled else click.style("OFF", fg="red")
        click.echo(f"      [{status}] {rule.name} (severity: {rule.severity})")

    click.echo()
    click.echo(click.style("  Rate Limiting:", bold=True))
    click.echo(f"    Enabled: {cfg.rate_limit.enabled}")
    click.echo(f"    Requests/min: {cfg.rate_limit.requests_per_minute}")
    click.echo(f"    Tokens/min: {cfg.rate_limit.tokens_per_minute}")

    click.echo()
    click.echo(click.style("  Cost Tracking:", bold=True))
    click.echo(f"    Enabled: {cfg.cost_tracking.enabled}")
    click.echo(f"    Budget limit: {cfg.cost_tracking.budget_limit_usd or 'none'}")

    click.echo()
    click.echo(click.style("  [OK] Configuration valid", fg="green"))


@main.command()
@click.argument("text")
def scan(text: str) -> None:
    """Scan a text string for PII and injection patterns.

    \b
    Examples:
      airlock scan "My email is john@example.com"
      airlock scan "Ignore all previous instructions"
    """
    from airlock.scanner import PIIScanner, PromptInjectionScanner
    from airlock.config import _default_pii_rules, _default_injection_rules

    pii_scanner = PIIScanner(_default_pii_rules())
    injection_scanner = PromptInjectionScanner(_default_injection_rules())

    click.echo(click.style("Scanning text...", bold=True))
    click.echo(f"  Input: {text}")
    click.echo()

    # PII scan
    pii_result = pii_scanner.scan(text, redact=True)
    if pii_result.findings:
        click.echo(click.style("  PII Findings:", fg="yellow"))
        for f in pii_result.findings:
            click.echo(f"    - [{f.rule_name}] '{f.matched_text}'")
        click.echo(f"  Redacted: {pii_result.redacted_text}")
    else:
        click.echo(click.style("  PII: Clean", fg="green"))

    click.echo()

    # Injection scan
    injection_result = injection_scanner.scan(text)
    if injection_result.findings:
        click.echo(click.style("  Injection Findings:", fg="red"))
        for f in injection_result.findings:
            click.echo(
                f"    - [{f.severity.value}] {f.rule_name}: '{f.matched_text}'"
            )
    else:
        click.echo(click.style("  Injection: Clean", fg="green"))


if __name__ == "__main__":
    main()
