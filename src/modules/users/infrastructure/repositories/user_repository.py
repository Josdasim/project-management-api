from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.users.domain.entities import User
from src.modules.users.infrastructure.models import User as UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        first_name=model.first_name,
        last_name=model.last_name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        model = UserModel(id=user.id, first_name=user.first_name, last_name=user.last_name)
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _to_entity(model) if User else None

    def update(self, user: User) -> User:
        model = self._session.get(UserModel, user.id)
        model.first_name = user.first_name
        model.last_name = user.last_name
        self._session.flush()
        return _to_entity(model)
