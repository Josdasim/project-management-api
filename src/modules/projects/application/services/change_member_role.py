from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository,
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import MemberWithUsername
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    MemberNotFoundError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class ChangeMemberRoleService:
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

    def change_role(
        self, *, project_id: UUID, actor_id: UUID, username: str, role: ProjectRole
    ) -> MemberWithUsername:
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

        if target.user_id == actor_id or target.role == ProjectRole.OWNER:
            raise ProjectPermissionDeniedError
        if actor.role == ProjectRole.ADMIN and ProjectRole.ADMIN in (target.role, role):
            raise ProjectPermissionDeniedError

        target.role = role
        updated = self._member.update(target)
        self._unit_work.commit()
        return MemberWithUsername(member=updated, username=account.username)
