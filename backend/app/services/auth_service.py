import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import RefreshSession, User
from app.schemas import UserCreate
from app.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int


def _new_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    settings = get_settings()
    lifetime_seconds = settings.access_token_minutes * 60
    token = create_access_token(
        user_id,
        settings.jwt_secret_key.get_secret_value(),
        settings.access_token_minutes,
    )
    return token, lifetime_seconds


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def register_user(session: AsyncSession, user_data: UserCreate) -> User:
    email = _normalize_email(str(user_data.email))
    user = User(email=email, password_hash=hash_password(user_data.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise EmailAlreadyRegisteredError from error
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User:
    user = await session.scalar(select(User).where(User.email == _normalize_email(email)))
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(password, password_hash)
    if user is None or not password_is_valid:
        raise InvalidCredentialsError
    return user


async def create_session(session: AsyncSession, user: User) -> AuthTokens:
    settings = get_settings()
    refresh_token = create_refresh_token()
    refresh_session = RefreshSession(
        family_id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    session.add(refresh_session)
    await session.commit()

    access_token, lifetime_seconds = _new_access_token(user.id)
    return AuthTokens(access_token, refresh_token, lifetime_seconds)


async def rotate_refresh_token(session: AsyncSession, raw_token: str) -> tuple[User, AuthTokens]:
    token_hash = hash_refresh_token(raw_token)
    refresh_session = await session.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )
    if refresh_session is None:
        raise InvalidRefreshTokenError

    now = datetime.now(UTC)
    if refresh_session.revoked_at is not None:
        await session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.family_id == refresh_session.family_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await session.commit()
        raise InvalidRefreshTokenError

    expires_at = refresh_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        refresh_session.revoked_at = now
        await session.commit()
        raise InvalidRefreshTokenError

    user = await session.get(User, refresh_session.user_id)
    if user is None:
        refresh_session.revoked_at = now
        await session.commit()
        raise InvalidRefreshTokenError

    successor_id = uuid.uuid4()
    next_refresh_token = create_refresh_token()
    successor = RefreshSession(
        id=successor_id,
        family_id=refresh_session.family_id,
        user_id=user.id,
        token_hash=hash_refresh_token(next_refresh_token),
        expires_at=now + timedelta(days=get_settings().refresh_token_days),
    )
    session.add(successor)
    await session.flush()

    rotation = await session.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == refresh_session.id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now, replaced_by_id=successor_id)
    )
    if rotation.rowcount != 1:
        await session.rollback()
        await session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.family_id == refresh_session.family_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await session.commit()
        raise InvalidRefreshTokenError

    await session.commit()
    access_token, lifetime_seconds = _new_access_token(user.id)
    return user, AuthTokens(access_token, next_refresh_token, lifetime_seconds)


async def revoke_refresh_token(session: AsyncSession, raw_token: str | None) -> None:
    if raw_token is None:
        return
    await session.execute(
        update(RefreshSession)
        .where(
            RefreshSession.token_hash == hash_refresh_token(raw_token),
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
