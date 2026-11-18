import pytest
from sqlalchemy import select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)


def delete(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


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
