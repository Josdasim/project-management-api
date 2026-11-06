from typing import Protocol

from src.modules.users.domain.entities import User

class UserRepository(Protocol):
    def add(self, user: User) -> User: ...
