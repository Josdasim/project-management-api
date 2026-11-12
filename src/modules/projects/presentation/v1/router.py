from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.core.pagination import PageResponse, PaginationParams
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.domain.exceptions import ProjectNameAlreadyExistsError
from src.modules.projects.presentation.dependencies import (
    get_create_project_service, get_list_projects_service
)
from src.modules.projects.presentation.v1.schemas import (
    CreateProjectRequest, ProjectResponse, ProjectListItem, ProjectListParams
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
    service: Annotated[ListProjectsService, Depends(get_list_projects_service)]
) -> PageResponse[ProjectListItem]:
    page = service.list_projects(
        user_id=account.user_id,
        search=params.search,
        page=params.page,
        page_size=params.page_size
    )

    return PageResponse[ProjectListItem](
        items=[
            ProjectListItem(
                id=item.project.id,
                name=item.project.name,
                description=item.project.description,
                status=item.project.status,
                created_at=item.project.created_at,
                role=item.role
            )
            for item in page.items
        ],
        total=page.total,
        page=page.page,
        page_size=page.page_size
    )