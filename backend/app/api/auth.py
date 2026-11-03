from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import auth_controller
from app.database import get_session
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    return await auth_controller.register(user_data, session)


@router.post("/login", response_model=AuthResponse, response_model_exclude_none=True)
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    return await auth_controller.login(request, response, credentials, session)


@router.post("/refresh", response_model=AuthResponse, response_model_exclude_none=True)
async def refresh(
    request: Request,
    response: Response,
    refresh_request: RefreshRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    return await auth_controller.refresh(
        request,
        response,
        refresh_request or RefreshRequest(),
        session,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    refresh_request: RefreshRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> Response:
    return await auth_controller.logout(
        request,
        response,
        refresh_request or RefreshRequest(),
        session,
    )


@router.get("/me", response_model=UserResponse)
async def current_user(
    user: User = Depends(get_current_user),
) -> User:
    return user
