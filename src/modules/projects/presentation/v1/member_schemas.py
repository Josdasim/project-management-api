from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from src.core.pagination import PaginationParams
from src.modules.projects.domain.entities import ProjectRole
from src.modules.projects.presentation.v1.schemas import SearchStr

UsernameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3)]


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: UsernameStr
    role: ProjectRole

    @field_validator("role")
    @classmethod
    def reject_owner(cls, value: ProjectRole) -> ProjectRole:
        if value == ProjectRole.OWNER:
            raise ValueError("No se puede asignar el rol de Propietario")
        return value


class MemberResponse(BaseModel):
    username: str
    role: ProjectRole
    joined_at: datetime


class MemberListParams(PaginationParams):
    search: SearchStr | None = None
    role: ProjectRole | None = None


class MemberListItem(BaseModel):
    username: str
    first_name: str
    last_name: str | None
    role: ProjectRole
    joined_at: datetime


class ChangeMemberRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: ProjectRole

    @field_validator("role")
    @classmethod
    def reject_owner(cls, value: ProjectRole) -> ProjectRole:
        if value == ProjectRole.OWNER:
            raise ValueError("No se puede asignar el rol de Propietario")
        return value
