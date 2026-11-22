from datetime import UTC, datetime

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.password_hasher import PasswordHasher
from src.modules.auth.application.interfaces.refresh_token_repository import RefreshTokenRepository
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.domain.exceptions import InvalidCurrentPasswordError


class DeactivateAccountService:
    def __init__(
        self,
        account: AccountRepository,
        refresh_token: RefreshTokenRepository,
        hasher: PasswordHasher,
        unit_work: UnitOfWork,
    ) -> None:
        self._account = account
        self._refresh_token = refresh_token
        self._hasher = hasher
        self._unit_work = unit_work

    def deactivate(self, *, account: Account, current_password: str) -> None:
        if not self._hasher.verify(current_password, account.password_hash):
            raise InvalidCurrentPasswordError

        self._account.update_status(account.id, AccountStatus.DEACTIVATED)
        self._refresh_token.revoke_all_for_account(account.id, datetime.now(UTC))
        self._unit_work.commit()
