from datetime import UTC, datetime
from uuid import uuid7

import pytest
from sqlalchemy import select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from tests.modules.projects.conftest import (
    PROJECTS_URL, access_token, bearer, create, other_token,
    add_member

)

def get_project(client, token, project_id):
    return client.get(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


# RF-PROJ-03-CA-01
def test_consultar_el_proyecto_como_propietario(client, access_token):
    project = create(client, access_token, name="Mi Proyecto", description="Descripción")

    response = get_project(client, access_token, project["id"])

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "name", "description", "status", "created_at", "role"}
    assert body["id"] == project["id"]
    assert body["role"] == "owner"


# RF-PROJ-03-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_consultar_el_proyecto_como_miembro_con_cualquier_rol(
    client, access_token, other_token, db, role
):
    project = create(client, other_token, name="Compartido")
    add_member(db, "Compartido", "dana_01", role)

    response = get_project(client, access_token, project["id"])

    assert response.status_code == 200
    assert response.json()["role"] == role.value


# RF-PROJ-03-CA-02
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token):
    project = create(client, other_token, name="Ajeno")

    assert get_project(client, access_token, project["id"]).status_code == 404


# RF-PROJ-03-CA-02
def test_responder_igual_si_el_proyecto_no_existe_o_no_es_miembro(
    client, access_token, other_token
):
    project = create(client, other_token, name="Ajeno")

    not_member = get_project(client, access_token, project["id"])
    not_found = get_project(client, access_token, uuid7())

    assert not_found.status_code == 404
    assert not_member.json() == not_found.json()


# RF-PROJ-03-CA-02
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db):
    project = create(client, access_token, name="Mi Proyecto")
    stored = db.scalar(select(ProjectModel))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    assert get_project(client, access_token, project["id"]).status_code == 404


# RF-PROJ-03-CA-02
def test_responder_no_encontrado_si_la_membresia_finalizo(client, access_token, other_token, db):
    project = create(client, other_token, name="Finalizado")
    add_member(db, "Finalizado", "dana_01", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert get_project(client, access_token, project["id"]).status_code == 404


# RF-PROJ-03-DERIVADO
def test_rechazar_un_id_que_no_es_uuid(client, access_token):
    assert get_project(client, access_token, "abc").status_code == 422


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(f"{PROJECTS_URL}/{uuid7()}").status_code == 401
