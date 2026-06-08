"""Application settings endpoints (admin only; secrets masked)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentAdmin, SessionDep
from app.models.car import Car
from app.models.user import User
from app.schemas.common import StatusResponse
from app.schemas.settings import SettingsUpdate, WipeRequest
from app.services import email_service, matrix_service, settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(_: CurrentAdmin, session: SessionDep) -> dict:
    # Returns the masked public shape directly (keys "1"/"from"/*_set match the
    # API contract exactly without alias-serialization concerns).
    cfg = await settings_service.load_all(session)
    return settings_service.to_public(cfg)


# Maps incoming PUT fields onto app_settings keys.
_SIMPLE_KEYS = {
    "fleet_name": "fleet_name",
    "timezone": "timezone",
    "default_locale": "default_locale",
    "currency": "currency",
    "daily_send_time": "daily_send_time",
    "tire_min_tread_mm": "tire_min_tread_mm",
}


@router.put("")
async def update_settings(
    payload: SettingsUpdate, _: CurrentAdmin, session: SessionDep
) -> dict:
    data = payload.model_dump(exclude_unset=True, by_alias=False)

    for field, key in _SIMPLE_KEYS.items():
        if field in data and data[field] is not None:
            await settings_service.set_value(session, key, str(data[field]))

    if data.get("default_lead_days"):
        lead = data["default_lead_days"]
        for idx in ("1", "2", "3"):
            attr = f"field_{idx}"
            if lead.get(attr) is not None:
                await settings_service.set_value(
                    session, f"default_lead_days_{idx}", str(lead[attr])
                )

    if data.get("smtp"):
        smtp = data["smtp"]
        mapping = {
            "host": "smtp_host",
            "port": "smtp_port",
            "encryption": "smtp_encryption",
            "username": "smtp_username",
            "from_": "smtp_from",
            "password": "smtp_password",
        }
        for attr, key in mapping.items():
            if attr in smtp and smtp[attr] is not None:
                await settings_service.set_value(session, key, str(smtp[attr]))

    if data.get("matrix"):
        matrix = data["matrix"]
        mapping = {
            "enabled": "matrix_enabled",
            "homeserver": "matrix_homeserver",
            "default_room": "matrix_default_room",
            "token": "matrix_token",
        }
        for attr, key in mapping.items():
            if attr in matrix and matrix[attr] is not None:
                val = matrix[attr]
                if attr == "enabled":
                    val = str(bool(val)).lower()
                await settings_service.set_value(session, key, str(val))

    await session.commit()
    cfg = await settings_service.load_all(session)
    return settings_service.to_public(cfg)


@router.post("/smtp/test", response_model=StatusResponse)
async def test_smtp(_: CurrentAdmin, session: SessionDep) -> StatusResponse:
    cfg = await settings_service.load_all(session)
    smtp = settings_service.smtp_config(cfg)
    if not smtp.get("host"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SMTP host is not configured"
        )
    to = smtp.get("from") or cfg.get("smtp_username")
    html = email_service.render_template(
        "expiring_document",
        cfg.get("default_locale", "sk"),
        {
            "car_name": "Test",
            "item_label": "STK",
            "item_name_sk": "STK",
            "item_name_en": "MOT inspection",
            "valid_until": "—",
            "days_left": 10,
            "overdue": False,
            "subject": "FleetCare SMTP test",
        },
    )
    try:
        await email_service.send_email(
            smtp=smtp, to=to, subject="FleetCare SMTP test", html_body=html
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"SMTP test failed: {exc}"
        ) from exc
    return StatusResponse(status="ok", detail=f"test email sent to {to}")


@router.post("/matrix/test", response_model=StatusResponse)
async def test_matrix(_: CurrentAdmin, session: SessionDep) -> StatusResponse:
    cfg = await settings_service.load_all(session)
    matrix_cfg = settings_service.matrix_config(cfg)
    try:
        await matrix_service.send_matrix(
            config=matrix_cfg, body="<p>FleetCare Matrix test</p>"
        )
    except matrix_service.MatrixDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Matrix test failed: {exc}"
        ) from exc
    return StatusResponse(status="ok", detail="matrix test message sent")


@router.get("/export")
async def export_settings(_: CurrentAdmin, session: SessionDep) -> dict:
    """JSON backup of settings (secrets masked)."""
    cfg = await settings_service.load_all(session)
    return settings_service.to_public(cfg)


@router.post("/wipe", status_code=status.HTTP_204_NO_CONTENT)
async def wipe(payload: WipeRequest, admin: CurrentAdmin, session: SessionDep) -> None:
    """Destructively delete all cars (cascades records) — admin + confirmation."""
    if not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required (confirm=true)",
        )
    from sqlalchemy import delete

    # Cascades remove all per-car records; users (except admins) and settings stay.
    await session.execute(delete(Car))
    await session.execute(
        delete(User).where(User.is_admin.is_(False))
    )
    await session.commit()
