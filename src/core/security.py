from argon2 import PasswordHasher as _Argon2

class ArgonPasswordHasher:
    def __init__(self) -> None:
        self._hasher = _Argon2()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)