from uuid import UUID

from src.core.pagination import Page
from src.modules.auth.public import AccountRepository
from src.modules.projects.application.interfaces.project_member_repository import (
    ProjectMemberRepository
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import MemberProfile
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import ProjectNotFoundError
from src.modules.users.public import UserRepository


class ListMembersService:
    def __init__(
        self,
        project: ProjectRepository,
        member: ProjectMemberRepository,
        account: AccountRepository,
        user: UserRepository
    ) -> None:
        self._project = project
        self._member = member
        self._account = account
        self._user = user

    def list_members(
        self, *,
        project_id: UUID,
        actor_id: UUID,
        search: str | None,
        role: ProjectRole | None,
        page: int,
        page_size: int
    ) -> Page[MemberProfile]:
        if self._project.get_by_id_and_member(project_id, actor_id) is None:
            raise ProjectNotFoundError

        members = self._member.list_active_by_project(project_id, role=role)
        user_ids = [member.user_id for member in members]
        accounts = {
            account.user_id: account for account in self._account.list_by_user_ids(user_ids)
            }
        users = {
            user.id: user for user in self._user.list_by_ids(user_ids)
        }

        items = []
        for member in members:
            account = accounts.get(member.user_id)
            user = users.get(member.user_id)

            items.append(
                MemberProfile(
                    username=account.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=member.role,
                    joined_at=member.joined_at
                )
            )

            if search:
                term = search.casefold()
                items = [
                    item for item in items if term in item.username.userfold()
                    or term in f"{item.first_name} {item.last_name or ''}".casefold()
                ]

            offset = (page - 1) * page_size
            return Page(
                items=items[offset : offset + page_size],
                total=len(items),
                page=page,
                page_size=page_size
            )