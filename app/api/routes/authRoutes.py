from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database.db import get_async_session
from app.models.models import User
from app.schemas.auth_schemas import (
    AuthResponse,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)


router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> AuthResponse:
    email = user_data.email.lower()
    result = await session.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise AppException(message="Email is already registered", status_code=409)

    user = User(email=email, hashed_password=hash_password(user_data.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AuthResponse(access_token=create_access_token(user.id), user=user)


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
) -> Token:
    email = form_data.username.lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AppException(message="Invalid email or password", status_code=401)

    if not user.is_active:
        raise AppException(message="User account is inactive", status_code=403)

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    current_user.first_name = user_data.first_name
    current_user.last_name = user_data.last_name
    current_user.country = user_data.country
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
