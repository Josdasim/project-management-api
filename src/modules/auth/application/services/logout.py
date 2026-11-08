from datetime import UTC, datetime

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.application.interfaces.refresh_token_repository import RefreshTokenRepository
from src.modules.auth.application.interfaces.token_provider import TokenProvider


class LogoutService:
    def __init__(
        self,
        refresh_token: RefreshTokenRepository,
        token_provider: TokenProvider,
        unit_work: UnitOfWork,
    ) -> None:
        self._refresh_token = refresh_token
        self._token_provider = token_provider
        self._unit_work = unit_work

    def logout(self, genereted_refresh_token: str) -> None:
        token_hash = self._token_provider.hash_refresh_token(genereted_refresh_token)
        stored = self._refresh_token.get_by_hash(token_hash)

        if stored is None or stored.revoked_at is not None:
            return

        stored.revoked_at = datetime.now(UTC)
        self._refresh_token.update(stored)
        self._unit_work.commit()
