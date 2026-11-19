from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.auth.public import Account, get_current_account
from src.modules.projects.public import ProjectNotFoundError
from src.modules.tasks.application.services.create_task import CreateTaskService
from src.modules.tasks.domain.exceptions import InvalidAssigneeError, TaskPermissionDeniedError
from src.modules.tasks.presentation.dependencies import get_create_task_service
from src.modules.tasks.presentation.v1.schemas import CreateTaskRequest, TaskResponse

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: UUID,
    payload: CreateTaskRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[CreateTaskService, Depends(get_create_task_service)],
) -> TaskResponse:
    try:
        detail = service.create(
            project_id=project_id,
            actor_id=account.user_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            assigned_to=payload.assigned_to,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para crear esta tarea"
        ) from None
    except InvalidAssigneeError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "El responsable indicado no es valido"
        ) from None

    return TaskResponse(
        id=detail.task.id,
        title=detail.task.title,
        description=detail.task.description,
        status=detail.task.status,
        priority=detail.task.priority,
        created_by=detail.created_by_username,
        assigned_to=detail.assigned_to_username,
        created_at=detail.task.created_at,
        updated_at=detail.task.updated_at,
    )
