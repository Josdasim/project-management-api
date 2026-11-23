from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.password_hasher import PasswordHasher
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import EmailAlreadyExistsError, InvalidCurrentPasswordError


class ChangeEmailService:
    def __init__(
        self, account: AccountRepository, hasher: PasswordHasher, unit_work: UnitOfWork
    ) -> None:
        self._account = account
        self._hasher = hasher
        self._unit_work = unit_work

    def change_email(
        self, *, account: Account, current_password: str, new_email: str
    ) -> Account:
        if not self._hasher.verify(current_password, account.password_hash):
            raise InvalidCurrentPasswordError

        new_email = new_email.strip().lower()
        if new_email == account.email:
            return account

        if self._account.email_exists(new_email):
            raise EmailAlreadyExistsError

        updated = self._account.update_email(account.id, new_email)
        self._unit_work.commit()
        return updated