from fastapi import HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, UserCreate, UserResponse
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    authenticate_user,
    create_session,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
COOKIE_TRANSPORT_HEADER = "x-auth-transport"


def _cookie_transport(request: Request) -> bool:
    return request.headers.get(COOKIE_TRANSPORT_HEADER) == "cookie"


def _require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin not in get_settings().cors_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origine non autorisée pour l'authentification par cookie.",
        )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    cookie_options = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
    }
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.access_token_minutes * 60,
        path="/",
        **cookie_options,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path="/auth",
        **cookie_options,
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    options = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
    }
    response.delete_cookie(ACCESS_COOKIE, path="/", **options)
    response.delete_cookie(REFRESH_COOKIE, path="/auth", **options)


def _auth_response(
    user: User,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> AuthResponse:
    settings = get_settings()
    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer" if access_token is not None else None,
        expires_in=settings.access_token_minutes * 60 if access_token is not None else None,
    )


async def register(
    user_data: UserCreate,
    session: AsyncSession,
) -> UserResponse:
    try:
        user = await register_user(session, user_data)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette adresse e-mail est déjà utilisée.",
        ) from error
    return UserResponse.model_validate(user)


async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    session: AsyncSession,
) -> AuthResponse:
    if _cookie_transport(request):
        _require_trusted_origin(request)

    try:
        user = await authenticate_user(session, str(credentials.email), credentials.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Adresse e-mail ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    tokens = await create_session(session, user)
    if _cookie_transport(request):
        _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
        return _auth_response(user)
    return _auth_response(user, tokens.access_token, tokens.refresh_token)


async def refresh(
    request: Request,
    response: Response,
    refresh_request: RefreshRequest,
    session: AsyncSession,
) -> AuthResponse:
    use_cookies = _cookie_transport(request)
    if use_cookies:
        _require_trusted_origin(request)
    token = request.cookies.get(REFRESH_COOKIE) if use_cookies else refresh_request.refresh_token
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton de renouvellement requis.",
        )

    try:
        user, tokens = await rotate_refresh_token(session, token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton de renouvellement invalide, expiré ou révoqué.",
        ) from error

    if use_cookies:
        _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
        return _auth_response(user)
    return _auth_response(user, tokens.access_token, tokens.refresh_token)


async def logout(
    request: Request,
    response: Response,
    refresh_request: RefreshRequest,
    session: AsyncSession,
) -> Response:
    use_cookies = _cookie_transport(request)
    if use_cookies:
        _require_trusted_origin(request)
    token = request.cookies.get(REFRESH_COOKIE) if use_cookies else refresh_request.refresh_token
    await revoke_refresh_token(session, token)
    if use_cookies:
        _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
