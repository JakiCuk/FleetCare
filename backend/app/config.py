"""Application configuration loaded from environment variables.

Exposes a singleton ``settings`` instance used across the backend.
Env var names mirror ``.env.example`` and ``docker-compose.yml``.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings sourced from the process environment.

    All fields have sensible defaults so the package stays importable even
    when an env var is missing (e.g. during tests or linting).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database / cache ────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://fleetcare:changeme@db:5432/fleetcare"
    redis_url: str = "redis://redis:6379/0"

    # ── Security / JWT ──────────────────────────────────────────────────
    jwt_secret: str = "please-change-me-to-a-long-random-string"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30
    jwt_algorithm: str = "HS256"

    # ── CORS ────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:8080"

    # ── Localization ────────────────────────────────────────────────────
    tz: str = "Europe/Bratislava"
    default_locale: str = "sk"

    # ── Initial admin (used by SQL agent's seed; read here for parity) ──
    admin_username: str = "admin"
    admin_password: str = "changeme"
    admin_email: str = "admin@fleetcare.local"

    seed_demo: bool = False

    # ── SMTP ────────────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_encryption: str = "tls"  # tls | ssl | none
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "FleetCare <fleet@example.com>"

    # ── Matrix ──────────────────────────────────────────────────────────
    matrix_enabled: bool = False
    matrix_homeserver: str = ""
    matrix_token: str = ""
    matrix_default_room: str = ""

    # ── Runtime ─────────────────────────────────────────────────────────
    run_migrations: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a clean list (comma-separated env value)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
