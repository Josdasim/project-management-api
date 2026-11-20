from datetime import UTC, datetime
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.member_task_unassigner import MemberTaskUnassigner
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository,
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class LeaveProjectService:
    def __init__(
        self,
        project: ProjectRepository,
        member: ProjectMemberRepository,
        tasks: MemberTaskUnassigner,
        unit_work: UnitOfWork,
    ) -> None:
        self._project = project
        self._member = member
        self._tasks = tasks
        self._unit_work = unit_work

    def leave(self, *, project_id: UUID, user_id: UUID) -> None:
        found = self._project.get_by_id_and_member(project_id, user_id)
        if found is None:
            raise ProjectNotFoundError
        if found.role == ProjectRole.OWNER:
            raise ProjectPermissionDeniedError

        member = self._member.get_by_project_and_user(project_id, user_id)
        member.left_at = datetime.now(UTC)
        self._member.update(member)
        self._tasks.unassign_member_tasks(project_id, user_id)
        self._unit_work.commit()
