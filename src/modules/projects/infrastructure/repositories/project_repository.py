from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.projects.domain.entities import Project
from src.modules.projects.domain.exceptions import ProjectNameAlreadyExistsError
from src.modules.projects.infrastructure.models import Project as ProjectModel


def _to_entity(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        description=model.description,
        status=model.status,
        deleted_at=model.deleted_at,
        created_at=model.created_at,
        updated_at=model.updated_at
    )

class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def name_exists(self, owner_id: UUID, name: str) -> bool:
        statement = select(
            exists().where(
                ProjectModel.owner_id == owner_id,
                func.lower(ProjectModel.name) == name.lower()
            )
        )

    def add(self, project: Project) -> Project:
        model = ProjectModel(
            id= project.id,
            owner_id = project.owner_id,
            name = project.name,
            description= project.description,
            status = project.status
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