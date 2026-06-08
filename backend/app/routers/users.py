"""User management endpoints (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import CurrentAdmin, SessionDep
from app.models.car import Car, UserCarGroup
from app.models.user import User
from app.routers._serializers import serialize_user
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


async def _sync_car_assignments(
    session: SessionDep, user: User, car_ids: list[int]
) -> None:
    """Replace a user's car assignments with ``car_ids`` (validating existence)."""
    if car_ids:
        existing = (
            await session.execute(select(Car.id).where(Car.id.in_(car_ids)))
        ).scalars().all()
        missing = set(car_ids) - set(existing)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown car id(s): {sorted(missing)}",
            )
    current = (
        await session.execute(
            select(UserCarGroup).where(UserCarGroup.user_id == user.id)
        )
    ).scalars().all()
    current_ids = {g.car_id for g in current}
    target_ids = set(car_ids)

    for group in current:
        if group.car_id not in target_ids:
            await session.delete(group)
    for cid in target_ids - current_ids:
        session.add(UserCarGroup(user_id=user.id, car_id=cid))


@router.get("", response_model=list[UserOut])
async def list_users(_: CurrentAdmin, session: SessionDep) -> list[UserOut]:
    users = (
        await session.execute(select(User).order_by(User.id))
    ).scalars().all()
    return [await serialize_user(session, u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate, _: CurrentAdmin, session: SessionDep
) -> UserOut:
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_admin=payload.is_admin,
        locale=payload.locale,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from exc
    await _sync_car_assignments(session, user, payload.car_ids)
    await session.commit()
    await session.refresh(user)
    return await serialize_user(session, user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int, _: CurrentAdmin, session: SessionDep
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await serialize_user(session, user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, payload: UserUpdate, _: CurrentAdmin, session: SessionDep
) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    car_ids = data.pop("car_ids", None)
    password = data.pop("password", None)
    if password is not None:
        user.hashed_password = hash_password(password)
    for field, value in data.items():
        setattr(user, field, value)

    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        ) from exc

    if car_ids is not None:
        await _sync_car_assignments(session, user, car_ids)
    await session.commit()
    await session.refresh(user)
    return await serialize_user(session, user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, admin: CurrentAdmin, session: SessionDep
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    await session.delete(user)
    await session.commit()
