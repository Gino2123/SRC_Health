from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.models import RefreshSession, User
from app.security import password_hasher


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
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


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_allows_web_origin_preflight(client: AsyncClient) -> None:
    response = await client.options(
        "/auth/register",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-auth-transport",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.asyncio
async def test_register_creates_user_without_returning_password_hash(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    password = "un-mot-de-passe-solide"
    response = await client.post(
        "/auth/register",
        json={"email": "Person@example.com", "password": password},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "person@example.com"
    assert "password_hash" not in response.json()

    async with session_factory() as session:
        user = await session.scalar(select(User).where(User.email == "person@example.com"))

    assert user is not None
    assert user.password_hash != password
    assert password_hasher.verify(password, user.password_hash)


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "person@example.com", "password": "un-mot-de-passe-solide"}
    first_response = await client.post("/auth/register", json=payload)
    duplicate_response = await client.post(
        "/auth/register",
        json={**payload, "email": "PERSON@example.com"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"email": "invalid", "password": "un-mot-de-passe-solide"},
        {"email": "person@example.com", "password": "trop-court"},
    ],
)
async def test_register_rejects_invalid_input(
    client: AsyncClient,
    payload: dict[str, str],
) -> None:
    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 422


async def _create_account(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/auth/register",
        json={"email": "auth@example.com", "password": "un-mot-de-passe-solide"},
    )
    assert response.status_code == 201
    return {"email": "auth@example.com", "password": "un-mot-de-passe-solide"}


async def _login_for_mobile(client: AsyncClient) -> dict[str, str]:
    credentials = await _create_account(client)
    response = await client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_login_returns_access_and_refresh_tokens(client: AsyncClient) -> None:
    credentials = await _create_account(client)
    response = await client.post("/auth/login", json=credentials)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 15 * 60
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


@pytest.mark.asyncio
async def test_login_rejects_incorrect_password(client: AsyncClient) -> None:
    await _create_account(client)
    response = await client.post(
        "/auth/login",
        json={"email": "auth@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_authenticates_user(client: AsyncClient) -> None:
    tokens = await _login_for_mobile(client)
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "auth@example.com"


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_replay_revokes_session_family(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    tokens = await _login_for_mobile(client)
    rotated = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != tokens["refresh_token"]

    async with session_factory() as session:
        stored_hashes = (await session.scalars(select(RefreshSession.token_hash))).all()
    assert tokens["refresh_token"] not in stored_hashes
    assert rotated.json()["refresh_token"] not in stored_hashes

    replay = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    after_replay = await client.post(
        "/auth/refresh",
        json={"refresh_token": rotated.json()["refresh_token"]},
    )

    assert replay.status_code == 401
    assert after_replay.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    tokens = await _login_for_mobile(client)
    response = await client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    after_logout = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 204
    assert after_logout.status_code == 401


@pytest.mark.asyncio
async def test_web_login_uses_httponly_cookies(client: AsyncClient) -> None:
    credentials = await _create_account(client)
    response = await client.post(
        "/auth/login",
        json=credentials,
        headers={
            "Origin": "http://localhost:3000",
            "X-Auth-Transport": "cookie",
        },
    )

    assert response.status_code == 200
    assert "access_token" not in response.json()
    assert "refresh_token" not in response.json()
    assert "httponly" in response.headers["set-cookie"].lower()

    current_user = await client.get("/auth/me")
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "auth@example.com"


@pytest.mark.asyncio
async def test_web_refresh_rotates_cookie_and_logout_clears_session(
    client: AsyncClient,
) -> None:
    credentials = await _create_account(client)
    headers = {
        "Origin": "http://localhost:3000",
        "X-Auth-Transport": "cookie",
    }
    login_response = await client.post("/auth/login", json=credentials, headers=headers)
    old_refresh_token = login_response.cookies.get("refresh_token")

    refresh_response = await client.post("/auth/refresh", headers=headers)
    new_refresh_token = refresh_response.cookies.get("refresh_token")
    logout_response = await client.post("/auth/logout", headers=headers)
    current_user_response = await client.get("/auth/me")

    assert login_response.status_code == 200
    assert refresh_response.status_code == 200
    assert old_refresh_token
    assert new_refresh_token
    assert old_refresh_token != new_refresh_token
    assert logout_response.status_code == 204
    assert current_user_response.status_code == 401


@pytest.mark.asyncio
async def test_web_cookie_login_rejects_untrusted_origin(client: AsyncClient) -> None:
    credentials = await _create_account(client)
    response = await client.post(
        "/auth/login",
        json=credentials,
        headers={
            "Origin": "https://attacker.example",
            "X-Auth-Transport": "cookie",
        },
    )

    assert response.status_code == 403
