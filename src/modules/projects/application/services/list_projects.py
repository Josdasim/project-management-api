from uuid import UUID

from src.core.pagination import Page
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import ProjectWithRole


class ListProjectsService:
    def __init__(self, project: ProjectRepository) -> None:
        self._project = project

    def list_projects(
        self, *, user_id: UUID, search: str | None, page: int, page_size: int
    ) -> Page[ProjectWithRole]:
        offset = (page - 1) * page_size
        items = self._project.list_by_member(user_id, search=search, limit=page_size, offset=offset)
        total = self._project.count_by_member(user_id, search=search)
        return Page(items=items, total=total, page=page, page_size=page_size)
