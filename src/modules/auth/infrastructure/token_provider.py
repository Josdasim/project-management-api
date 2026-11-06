import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.modules.auth.domain.exceptions import InvalidTokenError


class JwtTokenProvider:
    def __init__(
            self, secret_key: str, algorithm: str,
            access_token_expire_minutes: int
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = access_token_expire_minutes

    def create_access_token(self, account_id: UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(account_id),
            "iat": now,
            "exp": now + timedelta(minutes = self._expire_minutes)
        }

        return jwt.encode(payload, self._secret_key, algorithm = self._algorithm)

    def decode_access_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms = [self._algorithm],
                options = {
                    "require": ["exp", "sub"]
                }
            )

            return UUID(payload["sub"])
        except (jwt.PyJWTError, ValueError, KeyError) as error:
            raise InvalidTokenError from error

    def generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()