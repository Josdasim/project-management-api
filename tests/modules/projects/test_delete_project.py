from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel

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


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()["access_token"]


def create(client, token, **data):
    response = client.post(PROJECTS_URL, json=data, headers=bearer(token))

    assert response.status_code == 201
    return response.json()


def delete(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


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


# RF-PROJ-05-CA-01
def test_propietario_elimina_el_proyecto(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    assert delete(client, access_token, project["id"]).status_code == 204


# RF-PROJ-05-CA-01
def test_devolver_no_encontrado_al_consultar_un_proyecto_eliminado(client, access_token, db):
    project = create(client, access_token, name="Mi Proyecto")

    assert delete(client, access_token, project["id"]).status_code == 204

    db.expire_all()
    assert db.scalar(select(ProjectModel)).deleted_at is not None
    response = client.get(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token))
    assert response.status_code == 404
    listing = client.get(PROJECTS_URL, headers=bearer(access_token))
    assert listing.json()["total"] == 0


# RF-PROJ-05-CA-02
def test_rechazar_nombre_de_proyecto_eliminado(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")
    assert delete(client, access_token, project["id"]).status_code == 204

    response = client.post(PROJECTS_URL, json={"name": "mi proyecto"}, headers=bearer(access_token))

    assert response.status_code == 409


# RF-PROJ-05-CA-03
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_rechazar_eliminar_si_no_es_propietario(client, access_token, other_token, db, role):
    project = create(client, other_token, name="Compartido")
    add_member(db, "Compartido", "dana_01", role)

    assert delete(client, access_token, project["id"]).status_code == 403

    db.expire_all()
    assert db.scalar(select(ProjectModel)).deleted_at is None


# RF-PROJ-05-CA-04
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token):
    project = create(client, other_token, name="Ajeno")

    assert delete(client, access_token, project["id"]).status_code == 404


# RF-PROJ-05-CA-04
def test_responder_no_encontrado_si_ya_esta_eliminado(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")
    assert delete(client, access_token, project["id"]).status_code == 204

    assert delete(client, access_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = client.delete(f"{PROJECTS_URL}/{project['id']}")

    assert response.status_code == 401
