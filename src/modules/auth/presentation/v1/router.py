from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.application.services.change_email import ChangeEmailService
from src.modules.auth.application.services.change_password import ChangePasswordService
from src.modules.auth.application.services.deactivate_account import DeactivateAccountService
from src.modules.auth.application.services.login import LoginService
from src.modules.auth.application.services.logout import LogoutService
from src.modules.auth.application.services.refresh_session import RefreshSessionService
from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
)
from src.modules.auth.presentation.dependencies import (
    get_change_email_service,
    get_change_password_service,
    get_current_account,
    get_deactivate_account_service,
    get_login_service,
    get_logout_service,
    get_refresh_service,
    get_register_service,
)
from src.modules.auth.presentation.v1.schemas import (
    AccountResponse,
    ChangeEmailRequest,
    ChangePasswordRequest,
    DeactivateAccountRequest,
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
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El nombre de usuario ya esta registrado"
            ) from None
    except EmailAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El correo electronico ya esta registrado"
            ) from None

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
    service.logout(generated_refresh_token=payload.refresh_token)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ChangePasswordService, Depends(get_change_password_service)],
) -> None:
    try:
        service.change_password(
            account=account,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCurrentPasswordError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La contraseña actual no es correcta"
        ) from None


@router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(
    payload: DeactivateAccountRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[DeactivateAccountService, Depends(get_deactivate_account_service)],
) -> None:
    try:
        service.deactivate(account=account, current_password=payload.current_password)
    except InvalidCurrentPasswordError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La contraseña ingresada no es correcta"
        ) from None


@router.patch("/email", response_model=AccountResponse)
def change_email(
    payload: ChangeEmailRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ChangeEmailService, Depends(get_change_email_service)],
) -> AccountResponse:
    try:
        updated = service.change_email(
            account=account,
            current_password=payload.current_password,
            new_email=payload.new_email,
        )
    except InvalidCurrentPasswordError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La contraseña actual no es correcta"
        ) from None
    except EmailAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El correo electronico ya esta registrado"
        ) from None

    return AccountResponse(
        username=updated.username,
        email=updated.email,
        status=updated.status,
        created_at=updated.created_at,
    )