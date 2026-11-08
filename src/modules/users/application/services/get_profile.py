from uuid import UUID

from src.modules.users.application.interfaces.user_repository import UserRepository
from src.modules.users.domain.entities import User
from src.modules.users.domain.exceptions import UserNotFoundError


class GetProfileService:
    def __init__(self, user: UserRepository) -> None:
        self._user = user

    def get(self, user_id: UUID) -> User:
        user = self._user.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError

        return user
