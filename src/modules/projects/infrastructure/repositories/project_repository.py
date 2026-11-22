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

    def name_exists(
        self, owner_id: UUID, name: str, exclude_project_id: UUID | None = None
    ) -> bool:
        conditions = [
            ProjectModel.owner_id == owner_id,
            func.lower(ProjectModel.name) == name.lower(),
        ]
        if exclude_project_id is not None:
            conditions.append(ProjectModel.id != exclude_project_id)
        return bool(self._session.scalar(select(exists().where(*conditions))))

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

    def get_by_id_and_member(self, project_id: UUID, user_id: UUID) -> ProjectWithRole | None:
        statement = self._member_projects_statement(user_id, None).where(
            ProjectModel.id == project_id
        )
        row = self._session.execute(statement).first()

        if row is None:
            return None
        project, role = row

        return ProjectWithRole(project=_to_entity(project), role=role)

    def update(self, project: Project) -> Project:
        model = self._session.get(ProjectModel, project.id)
        model.name = project.name
        model.description = project.description
        model.deleted_at = project.deleted_at

        try:
            self._session.flush()
        except IntegrityError as error:
            constraint = getattr(error.orig.diag, "constraint_name", None) or ""

            if "lower_name" in constraint:
                raise ProjectNameAlreadyExistsError from error
            raise
        return _to_entity(model)

    def lock(self, project_id: UUID) -> None:
        self._session.execute(
            select(ProjectModel.id).where(ProjectModel.id == project_id).with_for_update()
        )

    def change_owner(self, project_id: UUID, owner_id: UUID) -> Project:
        model = self._session.get(ProjectModel, project_id)
        model.owner_id = owner_id

        try:
            self._session.flush()
        except IntegrityError as error:
            constraint = getattr(error.orig.diag, "constraint_name", None) or ""

            if "lower_name" in constraint:
                raise ProjectNameAlreadyExistsError from error
            raise
        return _to_entity(model)

    def _deleted_by_owner_statement(self, owner_id: UUID):
        return select(ProjectModel).where(
            ProjectModel.owner_id == owner_id, ProjectModel.deleted_at.is_not(None)
        )

    def get_by_id_and_owner(self, project_id: UUID, owner_id: UUID) -> Project | None:
        model = self._session.scalar(
            select(ProjectModel).where(
                ProjectModel.id == project_id, ProjectModel.owner_id == owner_id
            )
        )
        return _to_entity(model) if model else None

    def list_deleted_by_owner(self, owner_id: UUID, *, limit: int, offset: int) -> list[Project]:
        statement = (
            self._deleted_by_owner_statement(owner_id)
            .order_by(ProjectModel.deleted_at.desc(), ProjectModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(model) for model in self._session.scalars(statement)]

    def count_deleted_by_owner(self, owner_id: UUID) -> int:
        subquery = self._deleted_by_owner_statement(owner_id).subquery()
        return self._session.scalar(select(func.count()).select_from(subquery)) or 0

    def delete(self, project_id: UUID) -> None:
        model = self._session.get(ProjectModel, project_id)
        self._session.delete(model)
        self._session.flush()
