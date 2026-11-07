from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.users.application.services.get_profile import GetProfileService
from src.modules.users.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository
)


def get_profile_service(db: Annotated[Session, Depends(get_db)]) -> GetProfileService:
    return GetProfileService(user = SqlAlchemyUserRepository(db))

