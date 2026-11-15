from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.pagination import PageResponse, PaginationParams
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.delete_project import DeleteProjectService
from src.modules.projects.application.services.get_project import GetProjectService
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.application.services.update_project import UpdateProjectService
from src.modules.projects.application.services.add_member import AddMemberService
from src.modules.projects.domain.exceptions import (
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
    MemberAlreadyExistsError,
    MemberUserNotFoundError
)
from src.modules.projects.presentation.dependencies import (
    get_create_project_service,
    get_delete_project_service,
    get_list_projects_service,
    get_project_service,
    get_update_project_service,
    get_add_member_service
)
from src.modules.projects.presentation.v1.schemas import (
    CreateProjectRequest,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListParams,
    ProjectResponse,
    UpdateProjectRequest,
)
from src.modules.projects.presentation.v1.member_schemas import (
    MemberResponse, AddMemberRequest
)

router = APIRouter(prefix="/projects/{project_id}/members")

@router.post("", status_code=201)
def add_member(
    project_id: UUID,
    body: AddMemberRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[AddMemberService, Depends(get_add_member_service)]
) -> MemberResponse:
    try:
        added = service.add(
            project_id=project_id,
            actor_id=account.user_id,
            username=body.username,
            role=body.role
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "No tienes permiso para modificar este proyecto"
                ) from None
    except MemberUserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    except MemberAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El usuario ya es miembro del proyecto")
    return MemberResponse(
        username=added.username,
        role=added.member.role,
        joined_at=added.member.joined_at
    )