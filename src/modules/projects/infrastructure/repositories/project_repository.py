from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.projects.domain.entities import Project, ProjectWithRole
from src.modules.projects.domain.exceptions import ProjectNameAlreadyExistsError
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel


def _to_entity(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        description=model.description,
        status=model.status,
        deleted_at=model.deleted_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def name_exists(self, owner_id: UUID, name: str) -> bool:
        statement = select(
            exists().where(
                ProjectModel.owner_id == owner_id, func.lower(ProjectModel.name) == name.lower()
            )
        )

    def add(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            owner_id=project.owner_id,
            name=project.name,
            description=project.description,
            status=project.status,
        )
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as error:
            constraint = getattr(error.orig.diag, "constraint_name", None) or ""

            if "lower_name" in constraint:
                raise ProjectNameAlreadyExistsError from error
            raise
        return _to_entity(model)

    def _member_projects_statement(self, user_id: UUID, search: str | None):
        statement = (
            select(ProjectModel, ProjectMemberModel.role)
            .join(ProjectMemberModel, ProjectMemberModel.project_id == ProjectModel.id)
            .where(
                ProjectMemberModel.user_id == user_id,
                ProjectMemberModel.left_at.is_(None),
                ProjectModel.deleted_at.is_(None),
            )
        )
        if search:
            statement = statement.where(ProjectModel.name.icontains(search, autoescape=True))
        return statement

    def list_by_member(
        self, user_id: UUID, *, search: str | None, limit: int, offset: int
    ) -> list[ProjectWithRole]:
        statement = (
            self._member_projects_statement(user_id, search)
            .order_by(ProjectModel.created_at.desc(), ProjectModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = self._session.execute(statement).all()

        return [ProjectWithRole(project=_to_entity(project), role=role) for project, role in rows]

    def count_by_member(self, user_id: UUID, *, search: str | None) -> int:
        subquery = self._member_projects_statement(user_id, search).subquery()

        return self._session.scalar(select(func.count()).select_from(subquery)) or 0
