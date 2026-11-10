from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.application.services.login import LoginService
from src.modules.auth.application.services.logout import LogoutService
from src.modules.auth.application.services.refresh_session import RefreshSessionService
from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
)
from src.modules.auth.presentation.dependencies import (
    get_current_account,
    get_login_service,
    get_logout_service,
    get_refresh_service,
    get_register_service,
)
from src.modules.auth.presentation.v1.schemas import (
    AccountResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    service: Annotated[RegisterAccountService, Depends(get_register_service)],
) -> RegisterResponse:
    try:
        result = service.register(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El nombre de usuario ya esta registrado")
    except EmailAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo electronico ya esta registrado")

    return RegisterResponse(
        username=result.account.username,
        email=result.account.email,
        first_name=result.user.first_name,
        last_name=result.user.last_name,
        status=result.account.status,
        created_at=result.account.created_at,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest, service: Annotated[LoginService, Depends(get_login_service)]
) -> LoginResponse:
    try:
        result = service.login(identifier=payload.identifier, password=payload.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return LoginResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.get("/me", response_model=AccountResponse)
def read_current_account(
    account: Annotated[Account, Depends(get_current_account)],
) -> AccountResponse:
    return AccountResponse(
        username=account.username,
        email=account.email,
        status=account.status,
        created_at=account.created_at,
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    payload: RefreshRequest, service: Annotated[RefreshSessionService, Depends(get_refresh_service)]
) -> LoginResponse:
    try:
        result = service.refresh(generated_refresh_token=payload.refresh_token)
    except InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token de renovacion invalido",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return LoginResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest, service: Annotated[LogoutService, Depends(get_logout_service)]
) -> None:
    service.logout(genereted_refresh_token=payload.refresh_token)
