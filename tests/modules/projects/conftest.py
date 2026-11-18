from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel

# Por revisar en otros modulos de prueba
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PROJECTS_URL = "/api/v1/projects"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana01",
    "first_name": "Dana",
}
OTHER_USER = {**USER, "username": "otro_username", "email": "otro@correo.com"}

# Usados por las pruebas de projects


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()["access_token"]


def create(client, token, **data):
    return client.post(PROJECTS_URL, json=data, headers=bearer(token)).json()


def get_project(client, token, project_id):
    return client.get(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


def add_member(db, project_name, username, role, left_at=None):
    project = db.scalar(select(ProjectModel).where(ProjectModel.name == project_name))
    account = db.scalar(select(AccountModel).where(AccountModel.username == username))
    db.add(
        ProjectMemberModel(
            project_id=project.id,
            user_id=account.user_id,
            role=role,
            joined_at=datetime.now(UTC),
            left_at=left_at,
        )
    )
    db.commit()


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_token(client, "dana_01")


@pytest.fixture
def other_token(client):
    assert client.post(REGISTER_URL, json=OTHER_USER).status_code == 201
    return login_token(client, "otro_username")


@pytest.fixture
def third_token(client):
    data = {**USER, "username": "tercer_user", "email": "tercer@correo.com"}
    assert client.post(REGISTER_URL, json=data).status_code == 201
    return login_token(client, "tercer_user")


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")
