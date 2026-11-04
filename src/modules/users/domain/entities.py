from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class User:
    id: UUID
    first_name: str
    last_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None