from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from src.modules.projects.domain.entities import ProjectRole

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
