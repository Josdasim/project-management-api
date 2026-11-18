from datetime import UTC, datetime
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository,
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    MemberNotFoundError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class RemoveMemberService:
    def __init__(
        self,
        project: ProjectRepository,
        member: ProjectMemberRepository,
        account: AccountRepository,
        unit_work: UnitOfWork,
    ) -> None:
        self._project = project
        self._member = member
        self._account = account
        self._unit_work = unit_work

    def remove(self, *, project_id: UUID, actor_id: UUID, username: str) -> None:
        actor = self._project.get_by_id_and_member(project_id, actor_id)
        if actor is None:
            raise ProjectNotFoundError
        if actor.role not in (ProjectRole.OWNER, ProjectRole.ADMIN):
            raise ProjectPermissionDeniedError

        account = self._account.get_by_username(username)
        if account is None:
            raise MemberNotFoundError
        target = self._member.get_by_project_and_user(project_id, account.user_id)
        if target is None or target.left_at is not None:
            raise MemberNotFoundError

        if target.role == ProjectRole.OWNER:
            raise ProjectPermissionDeniedError
        if actor.role == ProjectRole.ADMIN and target.role == ProjectRole.ADMIN:
            raise ProjectPermissionDeniedError

        target.left_at = datetime.now(UTC)
        self._member.update(target)
        self._unit_work.commit()
