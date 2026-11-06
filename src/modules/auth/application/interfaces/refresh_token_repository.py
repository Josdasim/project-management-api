from typing import Protocol

from src.modules.auth.domain.entities import RefreshToken


class RefreshTokenRepository(Protocol):
    def add(self, token: RefreshToken) -> RefreshToken: ...
    def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...