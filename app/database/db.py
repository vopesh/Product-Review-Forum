from collections.abc import AsyncGenerator
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

database_url = make_url(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)
connect_args = {}

# asyncpg uses the `ssl` connect arg instead of the libpq-style `sslmode` URL param.
if database_url.query.get("sslmode") in {"require", "verify-ca", "verify-full"}:
    connect_args["ssl"] = True
    database_url = database_url.difference_update_query(["sslmode"])

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


class Base(DeclarativeBase):
    pass
