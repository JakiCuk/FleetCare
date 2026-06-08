"""Integration tests for the auth flow (login / me / refresh)."""

from __future__ import annotations

import pytest

from app.security import ACCESS_TOKEN_TYPE, decode_token


@pytest.mark.asyncio
async def test_login_returns_token_and_sets_refresh_cookie(client, admin_user) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"username": admin_user.username, "password": admin_user._plain_password},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == admin_user.username
    assert body["user"]["is_admin"] is True

    # Access token is a valid, correctly-typed JWT for this user.
    payload = decode_token(body["access_token"], expected_type=ACCESS_TOKEN_TYPE)
    assert payload["sub"] == str(admin_user.id)

    # Refresh token is delivered as an httpOnly cookie.
    set_cookie = resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie


@pytest.mark.asyncio
async def test_wrong_password_is_unauthorized(client, admin_user) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"username": admin_user.username, "password": "definitely-wrong"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_me_returns_current_user(client, admin_user) -> None:
    login = await client.post(
        "/api/auth/login",
        json={"username": admin_user.username, "password": admin_user._plain_password},
    )
    token = login.json()["access_token"]

    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    me = resp.json()
    assert me["username"] == admin_user.username
    assert me["email"] == admin_user.email
    assert isinstance(me["cars"], list)


@pytest.mark.asyncio
async def test_me_requires_authentication(client) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


def _extract_refresh_cookie(response) -> str:
    """Pull the refresh_token value out of the login Set-Cookie header.

    The cookie is ``Secure``, so httpx's jar won't persist it over plain http;
    parse the raw header instead.
    """
    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    token_part = set_cookie.split("refresh_token=", 1)[1]
    return token_part.split(";", 1)[0]


@pytest.mark.asyncio
async def test_refresh_issues_new_access_token(client, admin_user) -> None:
    login = await client.post(
        "/api/auth/login",
        json={"username": admin_user.username, "password": admin_user._plain_password},
    )
    refresh_value = _extract_refresh_cookie(login)
    assert refresh_value

    resp = await client.post(
        "/api/auth/refresh", cookies={"refresh_token": refresh_value}
    )
    assert resp.status_code == 200
    new_token = resp.json()["access_token"]
    payload = decode_token(new_token, expected_type=ACCESS_TOKEN_TYPE)
    assert payload["sub"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_refresh_without_cookie_is_unauthorized(client) -> None:
    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 401
