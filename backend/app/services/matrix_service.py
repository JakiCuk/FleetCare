"""Matrix notification sending via matrix-nio (guarded when disabled).

A globally-configured access token + homeserver is used to post an HTML notice
to a room (the global default room or a per-call override). Importing
``matrix-nio`` is deferred so the package stays importable even if the optional
dependency is unavailable at runtime.
"""

from __future__ import annotations

import html


class MatrixDisabledError(RuntimeError):
    """Raised when Matrix is disabled or not configured."""


async def send_matrix(
    *,
    config: dict,
    body: str,
    room: str | None = None,
) -> None:
    """Send an HTML message to a Matrix room.

    ``config`` is the dict returned by ``settings_service.matrix_config``.
    Raises :class:`MatrixDisabledError` when Matrix is disabled/unconfigured.
    """
    if not config.get("enabled"):
        raise MatrixDisabledError("Matrix integration is disabled")
    homeserver = config.get("homeserver")
    token = config.get("token")
    if not homeserver or not token:
        raise MatrixDisabledError("Matrix homeserver/token not configured")

    target_room = room or config.get("default_room")
    if not target_room:
        raise MatrixDisabledError("No Matrix room configured")

    # Deferred import: optional dependency.
    from nio import AsyncClient

    client = AsyncClient(homeserver)
    client.access_token = token
    try:
        # Resolve a room alias (#room:server) to an internal room id if needed.
        room_id = target_room
        if target_room.startswith("#"):
            resolved = await client.room_resolve_alias(target_room)
            room_id = getattr(resolved, "room_id", None) or target_room

        plain = _strip_html(body)
        await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": plain,
                "format": "org.matrix.custom.html",
                "formatted_body": body,
            },
        )
    finally:
        await client.close()


def _strip_html(value: str) -> str:
    """Very small HTML→text fallback for the plain ``body`` field."""
    import re

    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return " ".join(text.split())
