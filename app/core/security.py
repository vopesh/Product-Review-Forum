from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.database.db import get_async_session
from app.models.models import User


password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expires_at}
    return jwt.encode(payload, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    if credentials is None:
        raise AppException(message="Authentication required", status_code=401)

    try:
        payload = jwt.decode(credentials.credentials, settings.AUTH_SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM])
        user_id = payload.get("sub")
    except InvalidTokenError:
        raise AppException(message="Invalid authentication token", status_code=401)

    if not user_id:
        raise AppException(message="Invalid authentication token", status_code=401)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AppException(message="User not found or inactive", status_code=401)

    return user
