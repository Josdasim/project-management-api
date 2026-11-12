from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from src.modules.projects.infrastructure.repositories.project_member_repository import (
    SqlAlchemyProjectMemberRepository,
)

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
    return client.post(PROJECTS_URL, json=data, headers=bearer(token))


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_token(client, "dana_01")


@pytest.fixture
def other_token(client):
    assert client.post(REGISTER_URL, json=OTHER_USER).status_code == 201
    return login_token(client, "otro_username")


# RF-PROJ-01-CA-01 y CA-02
def test_crear_proyecto_con_datos_validos_y_quedar_como_propietario(client, access_token, db):
    response = create(client, access_token, name="Mi Proyecto", description="Descripción")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "name", "description", "status", "created_at"}
    assert body["name"] == "Mi Proyecto"
    assert body["status"] == "active"

    project = db.scalar(select(ProjectModel))
    member = db.scalar(select(ProjectMemberModel))
    assert member.project_id == project.id
    assert member.user_id == project.owner_id
    assert member.role == ProjectRole.OWNER
    assert member.left_at is None


# RF-PROJ-01-CA-01
def test_crear_proyecto_sin_descripcion(client, access_token):
    response = create(client, access_token, name="Mi Proyecto")

    assert response.status_code == 201
    assert response.json()["description"] is None


# RF-PROJ-01-CA-03
@pytest.mark.parametrize("name", ["", "   "])
def test_rechazar_nombre_vacio_o_solo_espacios(client, access_token, name):
    assert create(client, access_token, name=name).status_code == 422


# RF-PROJ-01-CA-03
@pytest.mark.parametrize("length, expected", [(100, 201), (101, 422)])
def test_validar_longitud_maxima_del_nombre(client, access_token, length, expected):
    assert create(client, access_token, name="a" * length).status_code == expected


# RF-PROJ-01-CA-03
@pytest.mark.parametrize("length, expected", [(5000, 201), (5001, 422)])
def test_validar_longitud_maxima_de_la_descripcion(client, access_token, length, expected):
    response = create(client, access_token, name="Mi Proyecto", description="a" * length)

    assert response.status_code == expected


# RF-PROJ-01-CA-03
def test_rechazar_nombre_repetido_sin_distinguir_mayusculas(client, access_token):
    assert create(client, access_token, name="Mi Proyecto").status_code == 201
    assert create(client, access_token, name="MI PROYECTO").status_code == 409


# RF-PROJ-01-REGLA
def test_permitir_el_mismo_nombre_a_otro_propietario(client, access_token, other_token):
    assert create(client, access_token, name="Mi Proyecto").status_code == 201
    assert create(client, other_token, name="Mi Proyecto").status_code == 201


# RF-PROJ-01-CA-03
def test_rechazar_nombre_de_un_proyecto_eliminado_logicamente(client, access_token, db):
    assert create(client, access_token, name="Mi Proyecto").status_code == 201
    project = db.scalar(select(ProjectModel))
    project.deleted_at = datetime.now(UTC)
    db.commit()

    assert create(client, access_token, name="Mi Proyecto").status_code == 409


# RF-PROJ-01-CA-04
def test_no_guardar_el_proyecto_si_falla_la_membresia(client, access_token, db, monkeypatch):
    def fail(self, member):
        raise RuntimeError("fallo forzado")

    monkeypatch.setattr(SqlAlchemyProjectMemberRepository, "add", fail)

    with pytest.raises(RuntimeError):
        create(client, access_token, name="Mi Proyecto")

    assert db.scalar(select(ProjectModel)) is None


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.post(PROJECTS_URL, json={"name": "Mi Proyecto"}).status_code == 401
