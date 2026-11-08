import uuid
from dataclasses import dataclass

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.password_hasher import PasswordHasher
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import EmailAlreadyExistsError, UsernameAlreadyExistsError
from src.modules.users.application.interfaces.user_repository import UserRepository
from src.modules.users.domain.entities import User


@dataclass(frozen=True)
class RegistrationResult:
    user: User
    account: Account


class RegisterAccountService:
    def __init__(
        self,
        accounts: AccountRepository,
        users: UserRepository,
        hasher: PasswordHasher,
        unit_work: UnitOfWork,
    ) -> None:
        self._account = accounts
        self._users = users
        self._hasher = hasher
        self._unit_work = unit_work

    def register(
        self,
        *,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str | None = None,
    ) -> RegistrationResult:
        username = username.strip().lower()
        email = email.strip().lower()

        if self._account.username_exists(username):
            raise UsernameAlreadyExistsError
        if self._account.email_exists(email):
            raise EmailAlreadyExistsError

        user = self._users.add(User(id=uuid.uuid7(), first_name=first_name, last_name=last_name))
        account = self._account.add(
            Account(
                id=uuid.uuid7(),
                user_id=user.id,
                username=username,
                email=email,
                password_hash=self._hasher.hash(password),
            )
        )
        self._unit_work.commit()
        return RegistrationResult(user=user, account=account)
