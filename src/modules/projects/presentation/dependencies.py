from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.auth.public import SqlAlchemyAccountRepository
from src.modules.projects.application.services.add_member import AddMemberService
from src.modules.projects.application.services.change_member_role import ChangeMemberRoleService
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.delete_project import DeleteProjectService
from src.modules.projects.application.services.get_project import GetProjectService
from src.modules.projects.application.services.list_members import ListMembersService
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.application.services.remove_member import RemoveMemberService
from src.modules.projects.application.services.update_project import UpdateProjectService
from src.modules.projects.application.services.leave_project import LeaveProjectService
from src.modules.projects.infrastructure.repositories.project_member_repository import (
    SqlAlchemyProjectMemberRepository,
)
from src.modules.projects.infrastructure.repositories.project_repository import (
    SqlAlchemyProjectRepository,
)
from src.modules.users.public import SqlAlchemyUserRepository


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
    return UpdateProjectService(project=SqlAlchemyProjectRepository(db), unit_work=db)


def get_delete_project_service(db: Annotated[Session, Depends(get_db)]) -> DeleteProjectService:
    return DeleteProjectService(project=SqlAlchemyProjectRepository(db), unit_work=db)


def get_add_member_service(db: Annotated[Session, Depends(get_db)]) -> AddMemberService:
    return AddMemberService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        account=SqlAlchemyAccountRepository(db),
        unit_work=db,
    )


def get_list_members_service(db: Annotated[Session, Depends(get_db)]) -> ListMembersService:
    return ListMembersService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        account=SqlAlchemyAccountRepository(db),
        user=SqlAlchemyUserRepository(db),
    )


def get_change_member_role_service(
    db: Annotated[Session, Depends(get_db)],
) -> ChangeMemberRoleService:
    return ChangeMemberRoleService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        account=SqlAlchemyAccountRepository(db),
        unit_work=db,
    )


def get_remove_member_service(db: Annotated[Session, Depends(get_db)]) -> RemoveMemberService:
    return RemoveMemberService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        account=SqlAlchemyAccountRepository(db),
        unit_work=db,
    )

def get_leave_project_service(db: Annotated[Session, Depends(get_db)]) -> LeaveProjectService:
    return LeaveProjectService(
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        unit_work=db,
    )