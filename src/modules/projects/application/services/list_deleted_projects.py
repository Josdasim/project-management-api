from uuid import UUID

from src.core.pagination import Page
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import Project


class ListDeletedProjectsService:
    def __init__(self, project: ProjectRepository) -> None:
        self._project = project

    def list_deleted(self, *, user_id: UUID, page: int, page_size: int) -> Page[Project]:
        offset = (page - 1) * page_size
        items = self._project.list_deleted_by_owner(user_id, limit=page_size, offset=offset)
        total = self._project.count_deleted_by_owner(user_id)
        return Page(items=items, total=total, page=page, page_size=page_size)
