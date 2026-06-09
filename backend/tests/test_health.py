"""Integration test for the health endpoint."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_ok(client) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    # DB connectivity is required for the suite to run at all.
    assert body["db"] == "ok"
    assert body["version"] == "0.2.0"
    # Redis may be unavailable in CI; overall status is then "degraded".
    assert body["status"] in ("ok", "degraded")
    assert body["redis"] in ("ok", "error")
