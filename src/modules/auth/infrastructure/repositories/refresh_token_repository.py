from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.modules.auth.domain.entities import RefreshToken
from src.modules.auth.infrastructure.models import RefreshToken as RefreshTokenModel


def _to_entity(model: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=model.id,
        account_id=model.account_id,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        created_at=model.created_at,
    )


class SqlAlchemyRefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            id=token.id,
            account_id=token.account_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            revoked_at=token.revoked_at,
        )
        self._session.add(model)
        self._session.flush()

        return _to_entity(model)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        model = self._session.scalar(statement)

        return _to_entity(model) if model else None

    def update(self, token: RefreshToken) -> None:
        model = self._session.get(RefreshTokenModel, token.id)
        model.revoked_at = token.revoked_at
        self._session.flush()

    def revoke_all_for_account(self, account_id: UUID, revoked_at: datetime) -> None:
        self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.account_id == account_id, RefreshTokenModel.revoked_at.is_(None)
            )
            .values(revoked_at=revoked_at)
        )
        self._session.flush()
