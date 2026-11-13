from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.pagination import PageResponse, PaginationParams
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.get_project import GetProjectService
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.domain.exceptions import (
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
)
from src.modules.projects.presentation.dependencies import (
    get_create_project_service,
    get_list_projects_service,
    get_project_service,
)
from src.modules.projects.presentation.v1.schemas import (
    CreateProjectRequest,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListParams,
    ProjectResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[CreateProjectRequest, Depends(get_create_project_service)],
) -> ProjectResponse:
    try:
        project = service.create(
            owner_id=account.user_id, name=payload.name, description=payload.description
        )
    except ProjectNameAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un proyecto con ese nombre"
        ) from None

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
    )


@router.get("", response_model=PageResponse[ProjectListItem])
def list_projects(
    params: Annotated[ProjectListParams, Query()],
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ListProjectsService, Depends(get_list_projects_service)],
) -> PageResponse[ProjectListItem]:
    page = service.list_projects(
        user_id=account.user_id, search=params.search, page=params.page, page_size=params.page_size
    )

    return PageResponse[ProjectListItem](
        items=[
            ProjectListItem(
                id=item.project.id,
                name=item.project.name,
                description=item.project.description,
                status=item.project.status,
                created_at=item.project.created_at,
                role=item.role,
            )
            for item in page.items
        ],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def read_project(
    project_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[GetProjectService, Depends(get_project_service)],
) -> ProjectDetailResponse:
    try:
        found = service.get(project_id=project_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None

    return ProjectDetailResponse(
        id=found.project.id,
        name=found.project.name,
        description=found.project.description,
        status=found.project.status,
        created_at=found.project.created_at,
        role=found.role,
    )
