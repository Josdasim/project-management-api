from sqlalchemy.orm import Session

from src.modules.projects.domain.entities import ProjectMember
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel


def _to_entity(model: ProjectMemberModel) -> ProjectMember:
    return ProjectMember(
        id=model.id,
        project_id=model.project_id,
        user_id=model.user_id,
        role=model.role,
        joined_at=model.joined_at,
        left_at=model.left_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyProjectMemberRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, member: ProjectMember) -> ProjectMember:
        model = ProjectMemberModel(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            left_at=member.left_at,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)
