from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.auth.domain.enums import AccountStatus

@dataclass
class Account:
    id: UUID
    user_id: UUID
    username: str
    email: str
    password_hash: str
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None