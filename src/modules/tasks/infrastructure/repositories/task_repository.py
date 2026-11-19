from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.tasks.domain.entities import Task
from src.modules.tasks.infrastructure.models import Task as TaskModel


def _to_entity(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        project_id=model.project_id,
        title=model.title,
        created_by=model.created_by,
        description=model.description,
        status=model.status,
        priority=model.priority,
        assigned_to=model.assigned_to,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyTaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> Task:
        model = TaskModel(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            created_by=task.created_by,
            assigned_to=task.assigned_to,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def get_by_id_and_project(self, task_id: UUID, project_id: UUID) -> Task | None:
        model = self._session.scalar(
            select(TaskModel).where(TaskModel.id == task_id, TaskModel.project_id == project_id)
        )
        return _to_entity(model) if model else None
