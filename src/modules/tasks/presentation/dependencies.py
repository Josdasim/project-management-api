from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.auth.public import SqlAlchemyAccountRepository
from src.modules.projects.public import (
    SqlAlchemyProjectMemberRepository,
    SqlAlchemyProjectRepository,
)
from src.modules.tasks.application.services.create_task import CreateTaskService
from src.modules.tasks.infrastructure.repositories.task_repository import SqlAlchemyTaskRepository


def get_create_task_service(db: Annotated[Session, Depends(get_db)]) -> CreateTaskService:
    return CreateTaskService(
        task=SqlAlchemyTaskRepository(db),
        project=SqlAlchemyProjectRepository(db),
        member=SqlAlchemyProjectMemberRepository(db),
        account=SqlAlchemyAccountRepository(db),
        unit_work=db,
    )
