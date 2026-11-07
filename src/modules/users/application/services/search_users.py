from dataclasses import dataclass

from src.modules.auth.public import AccountRepository, AccountStatus
from src.modules.users.application.interfaces.user_repository import UserRepository
from src.modules.users.domain.exceptions import UserNotFoundError


@dataclass(frozen = True)
class FoundUser:
    username: str
    first_name: str
    last_name: str | None

class SearchUsersService:
    def __init__(self, account: AccountRepository, user: UserRepository) -> None:
        self._account = account
        self._user = user

    def search(self,* , username: str | None, email: str | None) -> FoundUser:
        if username is not None:
            account = self._account.get_by_username(username.strip().lower())
        else:
            account = self._account.get_by_email((email or "").strip().lower())

        if account is None or account.status != AccountStatus.ACTIVE:
            raise UserNotFoundError

        user = self._user.get_by_id(account.user_id)

        if user is None:
            raise UserNotFoundError

        return FoundUser(
            username = account.username,
            first_name = user.first_name,
            last_name = user.last_name
        )