from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.pagination import PageResponse
from src.modules.auth.public import Account, get_current_account
from src.modules.projects.application.services.add_member import AddMemberService
from src.modules.projects.application.services.change_member_role import ChangeMemberRoleService
from src.modules.projects.application.services.leave_project import LeaveProjectService
from src.modules.projects.application.services.list_members import ListMembersService
from src.modules.projects.application.services.remove_member import RemoveMemberService
from src.modules.projects.domain.exceptions import (
    MemberAlreadyExistsError,
    MemberNotFoundError,
    MemberUserNotFoundError,
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)
from src.modules.projects.presentation.dependencies import (
    get_add_member_service,
    get_change_member_role_service,
    get_leave_project_service,
    get_list_members_service,
    get_remove_member_service,
)
from src.modules.projects.presentation.v1.member_schemas import (
    AddMemberRequest,
    ChangeMemberRoleRequest,
    MemberListItem,
    MemberListParams,
    MemberResponse,
)

router = APIRouter(prefix="/projects/{project_id}/members", tags=["members"])


@router.post("", status_code=201)
def add_member(
    project_id: UUID,
    body: AddMemberRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[AddMemberService, Depends(get_add_member_service)],
) -> MemberResponse:
    try:
        added = service.add(
            project_id=project_id, actor_id=account.user_id, username=body.username, role=body.role
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
        username=added.username, role=added.member.role, joined_at=added.member.joined_at
    )


@router.get("", response_model=PageResponse[MemberListItem])
def list_members(
    project_id: UUID,
    params: Annotated[MemberListParams, Query()],
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ListMembersService, Depends(get_list_members_service)],
) -> PageResponse[MemberListItem]:
    try:
        page = service.list_members(
            project_id=project_id,
            actor_id=account.user_id,
            search=params.search,
            role=params.role,
            page=params.page,
            page_size=params.page_size,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None

    return PageResponse[MemberListItem](
        items=[
            MemberListItem(
                username=item.username,
                first_name=item.first_name,
                last_name=item.last_name,
                role=item.role,
                joined_at=item.joined_at,
            )
            for item in page.items
        ],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.patch("/{username}", response_model=MemberResponse)
def change_member_role(
    project_id: UUID,
    username: str,
    payload: ChangeMemberRoleRequest,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[ChangeMemberRoleService, Depends(get_change_member_role_service)],
) -> MemberResponse:
    try:
        result = service.change_role(
            project_id=project_id,
            actor_id=account.user_id,
            username=username,
            role=payload.role,
        )
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except MemberNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miembro no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para cambiar el rol de este miembro"
        ) from None

    return MemberResponse(
        username=result.username, role=result.member.role, joined_at=result.member.joined_at
    )


@router.delete("/me", status_code=204)
def leave_project(
    project_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[LeaveProjectService, Depends(get_leave_project_service)],
) -> None:
    try:
        service.leave(project_id=project_id, user_id=account.user_id)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "El Propietario no puede abandonar el proyecto: debe transferir la propiedad o eliminarlo",
        ) from None


@router.delete("/{username}", status_code=204)
def remove_member(
    project_id: UUID,
    username: str,
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[RemoveMemberService, Depends(get_remove_member_service)],
) -> None:
    try:
        service.remove(project_id=project_id, actor_id=account.user_id, username=username)
    except ProjectNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except MemberNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Miembro no encontrado") from None
    except ProjectPermissionDeniedError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "No tienes permiso para retirar a este miembro"
        ) from None
