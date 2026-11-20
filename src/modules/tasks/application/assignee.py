from uuid import UUID

from src.modules.auth.public import Account, AccountStatus
from src.modules.projects.public import ProjectMemberRepository, ProjectRole
from src.modules.tasks.domain.exceptions import InvalidAssigneeError


def validate_assignee(
    member: ProjectMemberRepository, project_id: UUID, account: Account | None
) -> UUID:
    if account is None or account.status != AccountStatus.ACTIVE:
        raise InvalidAssigneeError

    membership = member.get_by_project_and_user(project_id, account.user_id)
    if (
        membership is None
        or membership.left_at is not None
        or membership.role == ProjectRole.VIEWER
    ):
        raise InvalidAssigneeError

    return account.user_id
