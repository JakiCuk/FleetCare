"""Async SMTP email sending with Jinja2 HTML templates (bilingual SK/EN).

Templates live in ``app/templates`` and are named ``<type>.<locale>.j2`` with a
fallback to ``<type>.sk.j2``. Configuration is read from the effective
``app_settings`` (which already layer the ``.env`` defaults).
"""

from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["j2", "html"]),
    enable_async=False,
)

_SUPPORTED_LOCALES = {"sk", "en"}


def render_template(template_type: str, locale: str, context: dict) -> str:
    """Render ``<type>.<locale>.j2`` (falling back to the SK variant)."""
    locale = locale if locale in _SUPPORTED_LOCALES else "sk"
    candidates = [f"{template_type}.{locale}.j2", f"{template_type}.sk.j2"]
    for name in candidates:
        try:
            template = _env.get_template(name)
        except Exception:  # noqa: BLE001 - missing template, try next
            continue
        return template.render(**context)
    # Last-resort plain body so notifications never hard-fail on a missing file.
    return f"<p>{context.get('subject', 'FleetCare notification')}</p>"


async def send_email(
    *,
    smtp: dict,
    to: str,
    subject: str,
    html_body: str,
) -> None:
    """Send an HTML email via SMTP. Raises on failure (caller logs status).

    ``smtp`` is the dict returned by ``settings_service.smtp_config``.
    """
    if not smtp.get("host"):
        raise RuntimeError("SMTP host is not configured")

    message = EmailMessage()
    message["From"] = smtp.get("from") or "FleetCare <fleet@example.com>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content("This message requires an HTML-capable client.")
    message.add_alternative(html_body, subtype="html")

    encryption = (smtp.get("encryption") or "tls").lower()
    use_tls = encryption == "ssl"  # implicit TLS on connect
    start_tls = encryption == "tls"  # STARTTLS upgrade

    await aiosmtplib.send(
        message,
        hostname=smtp["host"],
        port=int(smtp.get("port") or 587),
        username=smtp.get("username") or None,
        password=smtp.get("password") or None,
        use_tls=use_tls,
        start_tls=start_tls,
        timeout=30,
    )
