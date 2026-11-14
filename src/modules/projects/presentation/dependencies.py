from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.get_project import GetProjectService
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.application.services.update_project import UpdateProjectService
from src.modules.projects.infrastructure.repositories.project_member_repository import (
    SqlAlchemyProjectMemberRepository,
)
from src.modules.projects.infrastructure.repositories.project_repository import (
    SqlAlchemyProjectRepository,
)


def get_create_project_service(db: Annotated[Session, Depends(get_db)]) -> CreateProjectService:
    return CreateProjectService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        unit_work=db,
    )


def get_list_projects_service(db: Annotated[Session, Depends(get_db)]) -> ListProjectsService:
    return ListProjectsService(project=SqlAlchemyProjectRepository(db))


def get_project_service(db: Annotated[Session, Depends(get_db)]) -> GetProjectService:
    return GetProjectService(project=SqlAlchemyProjectRepository(db))


def get_update_project_service(db: Annotated[Session, Depends(get_db)]) -> UpdateProjectService:
    return UpdateProjectService(project=SqlAlchemyProjectRepository(db), unit_wort=db)
