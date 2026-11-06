from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import ArgonPasswordHasher
from src.modules.auth.application.services.register_account import RegisterAccountService
from src.modules.auth.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.modules.users.infrastructure.repositories import SqlAlchemyUserRepository


def get_register_service(
    db: Annotated[Session, Depends(get_db)]
) -> RegisterAccountService:
    return RegisterAccountService(
        accounts = SqlAlchemyAccountRepository(db),
        users = SqlAlchemyUserRepository(db),
        hasher = ArgonPasswordHasher(),
        unit_work = db
    )