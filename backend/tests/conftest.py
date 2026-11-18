import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401
from app.config import get_settings
from app.database import Base, get_session
from app.main import app


def _test_database_name() -> str:
    return f"{make_url(get_settings().database_url).database}_test"


def _test_database_url():  # noqa: ANN202
    return make_url(get_settings().database_url).set(database=_test_database_name())


async def _ensure_test_database() -> None:
    engine = create_async_engine(
        get_settings().database_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    name = _test_database_name()
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": name},
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{name}"'))
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _create_test_database() -> None:
    asyncio.run(_ensure_test_database())


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(_test_database_url(), poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()
