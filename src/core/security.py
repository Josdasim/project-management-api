from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerificationError


_DUMMY_HASH = _Argon2().hash("password-de-relleno-brominha")

class ArgonPasswordHasher:
    def __init__(self) -> None:
        self._hasher = _Argon2()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        try:
            self._hasher.verify(password_hash or _DUMMY_HASH, password)
        except (VerificationError, InvalidHashError):
            return False

        return password_hash is not None