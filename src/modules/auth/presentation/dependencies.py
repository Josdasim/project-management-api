from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.security import ArgonPasswordHasher
from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.modules.users.public import SqlAlchemyUserRepository
from src.modules.auth.application.services.login import LoginService
from src.modules.auth.infrastructure.repositories.refresh_token_repository import SqlAlchemyRefreshTokenRepository
from src.modules.auth.infrastructure.token_provider import JwtTokenProvider
from src.modules.auth.application.services.authenticate import AuthenticateService
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import InvalidTokenError
from src.modules.auth.application.services.refresh_session import RefreshSessionService
from src.modules.auth.application.services.logout import LogoutService

bearer_scheme = HTTPBearer(auto_error = False)


def _token_provider() -> JwtTokenProvider:
    return JwtTokenProvider(
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.access_token_expire_minutes
    )

def get_register_service(
    db: Annotated[Session, Depends(get_db)]
) -> RegisterAccountService:
    return RegisterAccountService(
        accounts = SqlAlchemyAccountRepository(db),
        users = SqlAlchemyUserRepository(db),
        hasher = ArgonPasswordHasher(),
        unit_work = db
    )

def get_login_service(db: Annotated[Session, Depends(get_db)]) -> LoginService:
    return LoginService(
        account = SqlAlchemyAccountRepository(db),
        refresh_token = SqlAlchemyRefreshTokenRepository(db),
        hasher = ArgonPasswordHasher(),
        token_provider = _token_provider(),
        unit_work = db,
        refresh_token_expire_days = settings.refresh_token_expire_days
    )

def get_authenticate_service(db: Annotated[Session, Depends(get_db)]) -> AuthenticateService:
    return AuthenticateService(
        account = SqlAlchemyAccountRepository(db),
        token_provider = _token_provider()
    )

def get_current_account(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: Annotated[AuthenticateService, Depends(get_authenticate_service)]
) -> Account:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "No autenticado",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized
    
    try:
        return service.authenticate(credentials.credentials)
    except InvalidTokenError:
        raise unauthorized from None

def get_refresh_service(db: Annotated[Session, Depends(get_db)]) -> RefreshSessionService:
    return RefreshSessionService(
        account=SqlAlchemyAccountRepository(db),
        refresh_token=SqlAlchemyRefreshTokenRepository(db),
        token_provider=JwtTokenProvider(
            settings.jwt_secret_key,
            settings.jwt_algorithm,
            settings.access_token_expire_minutes
        ),
        unit_work=db,
        refresh_token_expire_days=settings.refresh_token_expire_days
    )

def get_logout_service(db: Annotated[Session, Depends(get_db)]) -> LogoutService:
    return LogoutService(
        refresh_token=SqlAlchemyRefreshTokenRepository(db),
        token_provider=JwtTokenProvider(
            settings.jwt_secret_key,
            settings.jwt_algorithm,
            settings.access_token_expire_minutes
        ), unit_work=db
    )