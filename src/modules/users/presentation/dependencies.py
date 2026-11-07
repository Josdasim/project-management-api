from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.users.application.services.get_profile import GetProfileService
from src.modules.users.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository
)
from src.modules.users.application.services.update_profile import UpdateProfileService
from src.modules.users.application.services.search_users import SearchUsersService
from src.modules.auth.public import SqlAlchemyAccountRepository


def get_profile_service(db: Annotated[Session, Depends(get_db)]) -> GetProfileService:
    return GetProfileService(user = SqlAlchemyUserRepository(db))

def get_update_profile_service(db: Annotated[Session, Depends(get_db)]) -> UpdateProfileService:
    return UpdateProfileService(user = SqlAlchemyUserRepository(db), unit_work = db)

def get_search_users_service(db: Annotated[Session, Depends(get_db)]) -> SearchUsersService:
    return SearchUsersService(
        account = SqlAlchemyAccountRepository(db),
        user = SqlAlchemyUserRepository(db)
    )
