from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.users.application.interfaces.user_repository import UserRepository
from src.modules.users.domain.entities import User
from src.modules.users.domain.exceptions import UserNotFoundError


class UpdateProfileService:
    def __init__(self, user: UserRepository, unit_work: UnitOfWork) -> None:
        self._user = user
        self._unit_work = unit_work

    def update(self, user_id: UUID, changes: dict[str, str | None]) -> User:
        user = self._user.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError

        if "first_name" in changes:
            user.first_name = changes["first_name"]
        if "last_name" in changes:
            user.last_name = changes["last_name"]

        updated = self._user.update(user)
        self._unit_work.commit()
        return updated