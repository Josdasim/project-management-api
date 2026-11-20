from typing import Protocol
from uuid import UUID


class MemberTaskUnassigner(Protocol):
    def unassign_member_tasks(self, project_id: UUID, user_id: UUID) -> None: ...
