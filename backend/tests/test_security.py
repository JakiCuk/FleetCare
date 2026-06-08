"""Unit tests for password hashing (argon2) and JWT helpers (app.security).

Pure logic — no database, no app fixtures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── Password hashing ────────────────────────────────────────────────────────
def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret-pass")
    # argon2 hashes are prefixed and never equal the plaintext.
    assert hashed != "s3cret-pass"
    assert hashed.startswith("$argon2")
    assert verify_password("s3cret-pass", hashed) is True
    assert verify_password("wrong-pass", hashed) is False


def test_verify_password_handles_malformed_hash() -> None:
    # Must not raise on garbage input — returns False.
    assert verify_password("anything", "not-a-real-hash") is False


# ── JWT round-trips ─────────────────────────────────────────────────────────
def test_access_token_roundtrip() -> None:
    token = create_access_token(42)
    payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
    assert payload["sub"] == "42"
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert "exp" in payload and "jti" in payload


def test_refresh_token_roundtrip() -> None:
    token = create_refresh_token(7)
    payload = decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
    assert payload["sub"] == "7"
    assert payload["type"] == REFRESH_TOKEN_TYPE


def test_decode_rejects_wrong_token_type() -> None:
    access = create_access_token(1)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access, expected_type=REFRESH_TOKEN_TYPE)


def test_decode_rejects_expired_token() -> None:
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {
            "sub": "1",
            "type": ACCESS_TOKEN_TYPE,
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)


def test_decode_rejects_invalid_signature() -> None:
    forged = jwt.encode(
        {
            "sub": "1",
            "type": ACCESS_TOKEN_TYPE,
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        },
        "a-totally-different-secret",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(forged)
