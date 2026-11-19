from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.modules.tasks.domain.entities import Task
from src.modules.tasks.domain.enums import TaskPriority, TaskStatus
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

    def _project_tasks_statement(
        self,
        project_id: UUID,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: UUID | None,
        search: str | None,
    ):
        statement = select(TaskModel).where(TaskModel.project_id == project_id)
        if status is not None:
            statement = statement.where(TaskModel.status == status)
        if priority is not None:
            statement = statement.where(TaskModel.priority == priority)
        if assigned_to is not None:
            statement = statement.where(TaskModel.assigned_to == assigned_to)
        if search:
            statement = statement.where(
                or_(
                    TaskModel.title.icontains(search, autoescape=True),
                    TaskModel.description.icontains(search, autoescape=True),
                )
            )
        return statement

    def list_by_project(
        self,
        project_id: UUID,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: UUID | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> list[Task]:
        statement = (
            self._project_tasks_statement(project_id, status, priority, assigned_to, search)
            .order_by(TaskModel.created_at.desc(), TaskModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(model) for model in self._session.scalars(statement)]

    def count_by_project(
        self,
        project_id: UUID,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: UUID | None,
        search: str | None,
    ) -> int:
        subquery = self._project_tasks_statement(
            project_id, status, priority, assigned_to, search
        ).subquery()
        return self._session.scalar(select(func.count()).select_from(subquery)) or 0

    def update(self, task: Task) -> Task:
        model = self._session.get(TaskModel, task.id)
        model.title = task.title
        model.description = task.description
        model.status = task.status
        model.priority = task.priority
        model.assigned_to = task.assigned_to

        self._session.flush()
        self._session.refresh(model)
        return _to_entity(model)
