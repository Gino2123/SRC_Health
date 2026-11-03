import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: uuid.UUID, secret: str, lifetime_minutes: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=lifetime_minutes),
            "jti": str(uuid.uuid4()),
            "type": "access",
        },
        secret,
        algorithm="HS256",
    )


def decode_access_token(token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "exp", "type"]},
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
