import uuid

import pytest

from src.modules.tasks.infrastructure.models import Task as TaskModel
from tests.modules.projects.conftest import PROJECTS_URL, access_token, bearer, create


def create_task(client, token, project_id, data):
    return client.post(f"{PROJECTS_URL}/{project_id}/tasks", json=data, headers=bearer(token))


def new_task(client, token, project_id, **data):
    response = create_task(client, token, project_id, data)

    assert response.status_code == 201
    return response.json()


def set_status(db, task_id, status):
    task = db.get(TaskModel, uuid.UUID(task_id))
    task.status = status
    db.commit()


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")
