from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from src.modules.tasks.infrastructure.models import Task as TaskModel


class SqlAlchemyMemberTaskUnassigner:
    def __init__(self, session: Session) -> None:
        self._session = session

    def unassign_member_tasks(self, project_id: UUID, user_id: UUID) -> None:
        self._session.execute(
            update(TaskModel)
            .where(TaskModel.project_id == project_id, TaskModel.assigned_to == user_id)
            .values(assigned_to=None)
        )
        self._session.flush()
