from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository, AccountStatus
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository,
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import MemberWithUsername
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    InvalidNewOwnerError,
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class TransferOwnershipService:
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

    def transfer(self, *, project_id: UUID, actor_id: UUID, username: str) -> MemberWithUsername:
        self._project.lock(project_id)

        actor = self._project.get_by_id_and_member(project_id, actor_id)
        if actor is None:
            raise ProjectNotFoundError
        if actor.role != ProjectRole.OWNER:
            raise ProjectPermissionDeniedError

        account = self._account.get_by_username(username)
        if account is None or account.status != AccountStatus.ACTIVE or account.user_id == actor_id:
            raise InvalidNewOwnerError

        target = self._member.get_by_project_and_user(project_id, account.user_id)
        if target is None or target.left_at is not None:
            raise InvalidNewOwnerError

        project = actor.project
        if self._project.name_exists(account.user_id, project.name):
            raise ProjectNameAlreadyExistsError

        previous = self._member.get_by_project_and_user(project_id, actor_id)
        previous.role = ProjectRole.ADMIN
        self._member.update(previous)

        target.role = ProjectRole.OWNER
        self._member.update(target)

        project.owner_id = account.user_id
        self._project.update(project)

        self._unit_work.commit()

        return MemberWithUsername(member=target, username=account.username)
