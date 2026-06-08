"""Access layer for the ``app_settings`` key/value store.

Resolves effective configuration by layering, in order of precedence:
    1. a value stored in ``app_settings`` (admin-editable),
    2. the corresponding ``.env`` / environment default (``app.config.settings``).

Secrets (SMTP/Matrix credentials) are returned only as ``*_set: bool`` flags via
the settings router; the raw values returned here are for internal use
(email/matrix dispatch).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as env_settings
from app.models.settings import AppSetting

# Default values seeded conceptually (the SQL seed also writes these).
DEFAULTS: dict[str, str] = {
    "fleet_name": "FleetCare",
    "timezone": env_settings.tz,
    "default_locale": env_settings.default_locale,
    "currency": "EUR",
    "default_lead_days_1": "30",
    "default_lead_days_2": "14",
    "default_lead_days_3": "7",
    "daily_send_time": "08:00",
    "tire_min_tread_mm": "2.5",
    "smtp_host": env_settings.smtp_host,
    "smtp_port": str(env_settings.smtp_port),
    "smtp_encryption": env_settings.smtp_encryption,
    "smtp_username": env_settings.smtp_username,
    "smtp_password": env_settings.smtp_password,
    "smtp_from": env_settings.smtp_from,
    "matrix_enabled": str(env_settings.matrix_enabled).lower(),
    "matrix_homeserver": env_settings.matrix_homeserver,
    "matrix_token": env_settings.matrix_token,
    "matrix_default_room": env_settings.matrix_default_room,
}

SECRET_KEYS = {"smtp_password", "matrix_token"}


async def load_all(session: AsyncSession) -> dict[str, str]:
    """Return the effective settings dict (DB overrides over defaults)."""
    result = await session.execute(select(AppSetting))
    stored = {row.key: (row.value or "") for row in result.scalars().all()}
    effective = dict(DEFAULTS)
    effective.update({k: v for k, v in stored.items() if v is not None})
    return effective


async def get_value(session: AsyncSession, key: str, default: str | None = None) -> str | None:
    """Read a single setting (DB → DEFAULTS → provided default)."""
    row = await session.get(AppSetting, key)
    if row is not None and row.value is not None:
        return row.value
    return DEFAULTS.get(key, default)


async def set_value(session: AsyncSession, key: str, value: str | None) -> None:
    """Upsert a single setting value."""
    row = await session.get(AppSetting, key)
    if row is None:
        session.add(AppSetting(key=key, value=value))
    else:
        row.value = value


def _as_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, fallback: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _as_float(value: str | None, fallback: float | None = None) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def to_public(cfg: dict[str, str]) -> dict:
    """Shape the effective config into the masked public settings payload."""
    return {
        "fleet_name": cfg.get("fleet_name"),
        "timezone": cfg.get("timezone"),
        "default_locale": cfg.get("default_locale"),
        "currency": cfg.get("currency"),
        "default_lead_days": {
            "1": _as_int(cfg.get("default_lead_days_1"), 30),
            "2": _as_int(cfg.get("default_lead_days_2"), 14),
            "3": _as_int(cfg.get("default_lead_days_3"), 7),
        },
        "daily_send_time": cfg.get("daily_send_time"),
        "tire_min_tread_mm": _as_float(cfg.get("tire_min_tread_mm"), 2.5),
        "smtp": {
            "host": cfg.get("smtp_host") or None,
            "port": _as_int(cfg.get("smtp_port"), 587),
            "encryption": cfg.get("smtp_encryption"),
            "username": cfg.get("smtp_username") or None,
            "from": cfg.get("smtp_from") or None,
            "password_set": bool(cfg.get("smtp_password")),
        },
        "matrix": {
            "enabled": _as_bool(cfg.get("matrix_enabled")),
            "homeserver": cfg.get("matrix_homeserver") or None,
            "default_room": cfg.get("matrix_default_room") or None,
            "token_set": bool(cfg.get("matrix_token")),
        },
    }


def smtp_config(cfg: dict[str, str]) -> dict:
    """Internal SMTP config (includes secrets) for the email service."""
    return {
        "host": cfg.get("smtp_host") or "",
        "port": _as_int(cfg.get("smtp_port"), 587),
        "encryption": (cfg.get("smtp_encryption") or "tls").lower(),
        "username": cfg.get("smtp_username") or "",
        "password": cfg.get("smtp_password") or "",
        "from": cfg.get("smtp_from") or "FleetCare <fleet@example.com>",
    }


def matrix_config(cfg: dict[str, str]) -> dict:
    """Internal Matrix config (includes secrets) for the matrix service."""
    return {
        "enabled": _as_bool(cfg.get("matrix_enabled")),
        "homeserver": cfg.get("matrix_homeserver") or "",
        "token": cfg.get("matrix_token") or "",
        "default_room": cfg.get("matrix_default_room") or "",
    }
