"""Shared slowapi limiter (imported by main + auth router)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-IP limiter; in-memory storage is fine for a small self-hosted instance.
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# Limit string applied to authentication endpoints.
AUTH_RATE_LIMIT = "20/minute"
