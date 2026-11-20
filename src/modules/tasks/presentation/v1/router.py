from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.pagination import PageResponse
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.public import ProjectNotFoundError
from src.modules.tasks.application.services.assign_task import AssignTaskService
from src.modules.tasks.application.services.change_task_status import ChangeTaskStatusService
from src.modules.tasks.application.services.create_task import CreateTaskService
from src.modules.tasks.application.services.delete_task import DeleteTaskService
from src.modules.tasks.application.services.get_task import GetTaskService
from src.modules.tasks.application.services.list_tasks import ListTasksService
from src.modules.tasks.application.services.update_task import UpdateTaskService
from src.modules.tasks.domain.exceptions import (
    InvalidAssigneeError,
    InvalidStatusTransitionError,
    TaskNotEditableError,
    TaskNotFoundError,
    TaskPermissionDeniedError,
)
from src.modules.tasks.presentation.dependencies import (
    get_assign_task_service,
    get_change_task_status_service,
    get_create_task_service,
    get_delete_task_service,
    get_list_tasks_service,
    get_task_service,
    get_update_task_service,
)
from src.modules.tasks.presentation.v1.schemas import (
    AssignTaskRequest,
    ChangeTaskStatusRequest,
    CreateTaskRequest,
    TaskListParams,
    TaskResponse,
    UpdateTaskRequest,
)

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


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(
    project_id: UUID,
    task_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[GetTaskService, Depends(get_task_service)],
) -> TaskResponse:
    try:
        detail = service.get(project_id=project_id, task_id=task_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada") from None

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


@router.get("", response_model=PageResponse[TaskResponse])
def list_tasks(
    project_id: UUID,
    params: Annotated[TaskListParams, Query()],
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ListTasksService, Depends(get_list_tasks_service)],
) -> PageResponse[TaskResponse]:
    try:
        page = service.list_tasks(
            project_id=project_id,
            user_id=account.user_id,
            status=params.status,
            priority=params.priority,
            assigned_to=params.assigned_to,
            search=params.search,
            page=params.page,
            page_size=params.page_size,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None

    return PageResponse[TaskResponse](
        items=[
            TaskResponse(
                id=item.task.id,
                title=item.task.title,
                description=item.task.description,
                status=item.task.status,
                priority=item.task.priority,
                created_by=item.created_by_username,
                assigned_to=item.assigned_to_username,
                created_at=item.task.created_at,
                updated_at=item.task.updated_at,
            )
            for item in page.items
        ],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
def change_task_status(
    project_id: UUID,
    task_id: UUID,
    payload: ChangeTaskStatusRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ChangeTaskStatusService, Depends(get_change_task_status_service)],
) -> TaskResponse:
    try:
        detail = service.change_status(
            project_id=project_id,
            task_id=task_id,
            actor_id=account.user_id,
            status=payload.status,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada") from None
    except TaskPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para cambiar el estado de esta tarea"
        ) from None
    except InvalidStatusTransitionError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El cambio de estado solicitado no esta permitido"
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


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: UUID,
    task_id: UUID,
    payload: UpdateTaskRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[UpdateTaskService, Depends(get_update_task_service)],
) -> TaskResponse:
    try:
        detail = service.update(
            project_id=project_id,
            task_id=task_id,
            actor_id=account.user_id,
            changes=payload.model_dump(exclude_unset=True),
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada") from None
    except TaskPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para editar esta tarea"
        ) from None
    except TaskNotEditableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Una tarea completada o cancelada no se puede editar"
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


@router.patch("/{task_id}/assignee", response_model=TaskResponse)
def assign_task(
    project_id: UUID,
    task_id: UUID,
    payload: AssignTaskRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[AssignTaskService, Depends(get_assign_task_service)],
) -> TaskResponse:
    try:
        detail = service.assign(
            project_id=project_id,
            task_id=task_id,
            actor_id=account.user_id,
            assigned_to=payload.assigned_to,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada") from None
    except TaskPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para asignar esta tarea"
        ) from None
    except TaskNotEditableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede cambiar el responsable de una tarea completada o cancelada",
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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: UUID,
    task_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[DeleteTaskService, Depends(get_delete_task_service)],
) -> None:
    try:
        service.delete(project_id=project_id, task_id=task_id, actor_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except TaskNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada") from None
    except TaskPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tiene permiso para eliminar esta tarea"
        ) from None
