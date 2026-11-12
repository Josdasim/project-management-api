from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.exceptions import EmailAlreadyExistsError, UsernameAlreadyExistsError
from src.modules.auth.infrastructure.models import Account as AccountModel


def _to_entity(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        user_id=model.user_id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.created_at,
    )


class SqlAlchemyAccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def username_exists(self, username: str) -> bool:
        statement = select(exists().where(AccountModel.username == username))
        return bool(self._session.scalar(statement))

    def email_exists(self, email: str) -> bool:
        statement = select(exists().where(AccountModel.email == email))
        return bool(self._session.scalar(statement))

    def add(self, account: Account) -> Account:
        model = AccountModel(
            id=account.id,
            user_id=account.user_id,
            username=account.username,
            email=account.email,
            password_hash=account.password_hash,
            status=account.status,
        )
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            constraint = getattr(error.orig.diag, "constraint_name", None) or ""
            if "username" in constraint:
                raise UsernameAlreadyExistsError from error
            if "email" in constraint:
                raise EmailAlreadyExistsError from error
            raise
        return _to_entity(model)

    def get_by_username(self, username: str) -> Account | None:
        statament = select(AccountModel).where(AccountModel.username == username)
        model = self._session.scalar(statament)
        return _to_entity(model) if model else None

    def get_by_email(self, email: str) -> Account | None:
        statement = select(AccountModel).where(AccountModel.email == email)
        model = self._session.scalar(statement)
        return _to_entity(model) if model else None

    def get_by_id(self, account_id: UUID) -> Account | None:
        model = self._session.get(AccountModel, account_id)
        return _to_entity(model) if model else None
