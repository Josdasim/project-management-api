import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.refresh_token_repository import RefreshTokenRepository
from src.modules.auth.application.interfaces.token_provider import TokenProvider
from src.modules.auth.domain.entities import AccountStatus, RefreshToken
from src.modules.auth.domain.exceptions import InvalidTokenError


@dataclass(frozen=True)
class RefreshResult:
    access_token: str
    refresh_token: str


class RefreshSessionService:
    def __init__(
        self,
        account: AccountRepository,
        refresh_token: RefreshTokenRepository,
        token_provider: TokenProvider,
        unit_work: UnitOfWork,
        refresh_token_expire_days: int,
    ) -> None:
        self._account = account
        self._refresh_token = refresh_token
        self._token_provider = token_provider
        self._unit_work = unit_work
        self._expire_days = refresh_token_expire_days

    def refresh(self, generated_refresh_token: str) -> RefreshResult:
        now = datetime.now(UTC)
        token_hash = self._token_provider.hash_refresh_token(generated_refresh_token)
        stored = self._refresh_token.get_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenError

        if stored.revoked_at is not None:
            self._refresh_token.revoke_all_for_account(stored.account_id, now)
            self._unit_work.commit()
            raise InvalidTokenError

        if stored.expires_at <= now:
            raise InvalidTokenError

        account = self._account.get_by_id(stored.account_id)
        if account is None or account.status != AccountStatus.ACTIVE:
            raise InvalidTokenError

        
        stored.revoked_at = now
        self._refresh_token.update(stored)

        new_generated_token = self._token_provider.generate_refresh_token()
        self._refresh_token.add(
            RefreshToken(
                id=uuid.uuid7(),
                account_id=account.id,
                token_hash=self._token_provider.hash_refresh_token(new_generated_token),
                expires_at=now + timedelta(days=self._expire_days),
            )
        )
        access = self._token_provider.create_access_token(account.id)
        self._unit_work.commit()
        return RefreshResult(access_token=access, refresh_token=new_generated_token)

