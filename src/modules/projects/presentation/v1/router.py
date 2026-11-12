from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.create_project import (
    CreateProjectService
)
from src.modules.projects.domain.exceptions import ProjectNameAlreadyExistsError
from src.modules.projects.presentation.dependencies import get_create_project_service
from src.modules.projects.presentation.v1.schemas import (
    CreateProjectRequest, ProjectResponse
)

router = APIRouter(prefix='/projects', tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[CreateProjectRequest, Depends(get_create_project_service)]
) -> ProjectResponse:
    try:
        project = service.create(
            owner_id = account.user_id,
            name = payload.name,
            description=payload.description
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
        created_at=project.created_at
    )
    