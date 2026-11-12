from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from src.core.pagination import PaginationParams, PageResponse
from src.modules.projects.domain.enums import ProjectStatus, ProjectRole

NAME_MAX = 100
DESCRIPTION_MAX = 5000

ProjectNameStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX)
]
DescriptionStr = Annotated[str, StringConstraints(max_length=DESCRIPTION_MAX)]
SearchStr =  Annotated[str, StringConstraints(strip_whitespace=True, max_length=NAME_MAX)]

class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ProjectNameStr
    description: DescriptionStr | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime

class ProjectListParams(PaginationParams):
    search: SearchStr | None = None

class ProjectListItem(ProjectResponse):
    role: ProjectRole
