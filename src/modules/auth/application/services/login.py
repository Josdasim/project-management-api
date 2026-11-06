import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.password_hasher import PasswordHasher
from src.modules.auth.application.interfaces.refresh_token_repository import RefreshTokenRepository
from src.modules.auth.application.interfaces.token_provider import TokenProvider
from src.modules.auth.domain.entities import RefreshToken
from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.domain.exceptions import InvalidCredentialsError


@dataclass(frozen = True)
class LoginResult:
    access_token: str
    refresh_token: str


class LoginService:
    def __init__(
            self, account: AccountRepository,
            refresh_token: RefreshTokenRepository,
            hasher: PasswordHasher,
            token_provider: TokenProvider,
            unit_work: UnitOfWork,
            refresh_token_expire_days: int
    ) -> None:
        self._account = account
        self._refresh_token = refresh_token
        self._hasher = hasher
        self._token_provider = token_provider
        self._unit_work = unit_work
        self._refresh_days = refresh_token_expire_days

    def login(self, *, identifier: str, password: str) -> LoginResult:
        identifier = identifier.strip().lower()

        if "@" in identifier:
            account = self._account.get_by_email(identifier)
        else:
            account = self._account.get_by_username(identifier) 

        is_password_ok = self._hasher.verify(password, account.password_hash if account else None)

        if account is None or not is_password_ok or account.status != AccountStatus.ACTIVE:
            raise InvalidCredentialsError

        generated_refresh_token = self._token_provider.generate_refresh_token()
        self._refresh_token.add(
            RefreshToken(
                id = uuid.uuid7(),
                account_id = account.id,
                token_hash = self._token_provider.hash_refresh_token(generated_refresh_token),
                expires_at = datetime.now() + timedelta(days = self._refresh_days)
            )
        )
        self._unit_work.commit()

        return LoginResult(
            access_token = self._token_provider.create_access_token(account.id),
            refresh_token = generated_refresh_token
        )