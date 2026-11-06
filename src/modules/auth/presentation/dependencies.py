from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.security import ArgonPasswordHasher
from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from src.modules.auth.application.services.login import LoginService
from src.modules.auth.infrastructure.repositories.refresh_token_repository import SqlAlchemyRefreshTokenRepository
from src.modules.auth.infrastructure.token_provider import JwtTokenProvider


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
        token_provider = JwtTokenProvider(
            settings.jwt_secret_key,
            settings.jwt_algorithm,
            settings.access_token_expire_minutes
        ),
        unit_work = db,
        refresh_token_expire_days = settings.refresh_token_expire_days
    )
