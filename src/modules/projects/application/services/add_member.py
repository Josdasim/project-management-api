from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid7

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository, AccountStatus
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository,
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import MemberWithUsername, ProjectMember
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    MemberAlreadyExistsError,
    MemberUserNotFoundError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class AddMemberService:
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

    def add(
        self, *, project_id: UUID, actor_id: UUID, username: str, role: ProjectRole
    ) -> MemberWithUsername:
        actor = self._project.get_by_id_and_member(project_id, actor_id)

        if actor is None:
            raise ProjectNotFoundError
        if actor.role not in (ProjectRole.OWNER, ProjectRole.ADMIN):
            raise ProjectPermissionDeniedError
        if role == ProjectRole.ADMIN and actor.role != ProjectRole.OWNER:
            raise ProjectPermissionDeniedError

        account = self._account.get_by_username(username)
        if account is None or account.status != AccountStatus.ACTIVE:
            raise MemberUserNotFoundError

        now = datetime.now(UTC)
        existing = self._member.get_by_project_and_user(project_id, account.user_id)
        if existing is None:
            member = self._member.add(
                ProjectMember(
                    id=uuid7(),
                    project_id=project_id,
                    user_id=account.user_id,
                    role=role,
                    joined_at=now,
                )
            )
        elif existing.left_at is None:
            raise MemberAlreadyExistsError
        else:
            existing.role = role
            existing.joined_at = now
            existing.left_at = None
            member = self._member.update(existing)

        self._unit_work.commit()
        return MemberWithUsername(member=member, username=account.username)
