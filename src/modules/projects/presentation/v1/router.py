from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.pagination import PageResponse, PaginationParams
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.create_project import CreateProjectService
from src.modules.projects.application.services.delete_project import DeleteProjectService
from src.modules.projects.application.services.delete_project_permanently import (
    DeleteProjectPermanentlyService,
)
from src.modules.projects.application.services.get_project import GetProjectService
from src.modules.projects.application.services.list_deleted_projects import (
    ListDeletedProjectsService,
)
from src.modules.projects.application.services.list_projects import ListProjectsService
from src.modules.projects.application.services.restore_project import RestoreProjectService
from src.modules.projects.application.services.transfer_ownership import TransferOwnershipService
from src.modules.projects.application.services.update_project import UpdateProjectService
from src.modules.projects.domain.exceptions import (
    InvalidNewOwnerError,
    ProjectNameAlreadyExistsError,
    ProjectNotDeletedError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)
from src.modules.projects.presentation.dependencies import (
    get_create_project_service,
    get_delete_project_permanently_service,
    get_delete_project_service,
    get_list_deleted_projects_service,
    get_list_projects_service,
    get_project_service,
    get_restore_project_service,
    get_transfer_ownership_service,
    get_update_project_service,
)
from src.modules.projects.presentation.v1.member_schemas import MemberResponse
from src.modules.projects.presentation.v1.schemas import (
    CreateProjectRequest,
    DeletedProjectItem,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectListParams,
    ProjectResponse,
    TransferOwnershipRequest,
    UpdateProjectRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[CreateProjectService, Depends(get_create_project_service)],
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


@router.get("/deleted", response_model=PageResponse[DeletedProjectItem])
def list_deleted_projects(
    params: Annotated[PaginationParams, Query()],
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ListDeletedProjectsService, Depends(get_list_deleted_projects_service)],
) -> PageResponse[DeletedProjectItem]:
    page = service.list_deleted(
        user_id=account.user_id, page=params.page, page_size=params.page_size
    )

    return PageResponse[DeletedProjectItem](
        items=[
            DeletedProjectItem(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                deleted_at=project.deleted_at,
            )
            for project in page.items
        ],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.post("/{project_id}/restore", response_model=ProjectDetailResponse)
def restore_project(
    project_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[RestoreProjectService, Depends(get_restore_project_service)],
) -> ProjectDetailResponse:
    try:
        restored = service.restore(project_id=project_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectNotDeletedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El proyecto no esta eliminado") from None

    return ProjectDetailResponse(
        id=restored.project.id,
        name=restored.project.name,
        description=restored.project.description,
        status=restored.project.status,
        created_at=restored.project.created_at,
        role=restored.role,
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


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
def update_project(
    project_id: UUID,
    payload: UpdateProjectRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[UpdateProjectService, Depends(get_update_project_service)],
) -> ProjectDetailResponse:

    try:
        updated = service.update(
            project_id=project_id,
            user_id=account.user_id,
            changes=payload.model_dump(exclude_unset=True),
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para modificar este proyecto"
        ) from None
    except ProjectNameAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un proyecto con ese nombre"
        ) from None

    return ProjectDetailResponse(
        id=updated.project.id,
        name=updated.project.name,
        description=updated.project.description,
        status=updated.project.status,
        created_at=updated.project.created_at,
        role=updated.role,
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[DeleteProjectService, Depends(get_delete_project_service)],
) -> None:
    try:
        service.delete(project_id=project_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para modificar este proyecto"
        ) from None


@router.post("/{project_id}/transfer-ownership", response_model=MemberResponse)
def transfer_ownership(
    project_id: UUID,
    payload: TransferOwnershipRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[TransferOwnershipService, Depends(get_transfer_ownership_service)],
) -> MemberResponse:
    try:
        result = service.transfer(
            project_id=project_id, actor_id=account.user_id, username=payload.username
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Solo el propietario puede transferir el proyecto"
        ) from None
    except InvalidNewOwnerError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El nuevo propietario indicado no es valido"
        ) from None
    except ProjectNameAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El nuevo propietario ya tiene un proyecto con ese nombre; cambialo antes de transferir",
        ) from None

    return MemberResponse(
        username=result.username, role=result.member.role, joined_at=result.member.joined_at
    )


@router.delete("/{project_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_permanently(
    project_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[
        DeleteProjectPermanentlyService, Depends(get_delete_project_permanently_service)
    ],
) -> None:
    try:
        service.delete_permanently(project_id=project_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectNotDeletedError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede eliminar permanentemente un proyecto que este en la papelera",
        ) from None
