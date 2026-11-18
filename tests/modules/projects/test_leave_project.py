import pytest

from src.modules.projects.domain.enums import ProjectRole
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    get_project,
    other_token,
)


def leave(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}/members/me", headers=bearer(token))


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")


# RF-MEM-05-CA-01
def test_miembro_abandona_el_proyecto(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = leave(client, other_token, project["id"])

    assert response.status_code == 204
    assert get_project(client, other_token, project["id"]).status_code == 404
    listing = client.get(f"{PROJECTS_URL}/{project['id']}/members", headers=bearer(access_token))
    assert [item["username"] for item in listing.json()["items"]] == ["dana_01"]


# RF-MEM-05-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.VIEWER])
def test_administrador_y_observador_abandonan(client, access_token, other_token, db, project, role):
    add_member(db, "Mi Proyecto", "otro_username", role)

    assert leave(client, other_token, project["id"]).status_code == 204


# RF-MEM-05-CA-02
def test_rechazar_que_el_propietario_abandone(client, access_token, project):
    response = leave(client, access_token, project["id"])

    assert response.status_code == 403
    assert get_project(client, access_token, project["id"]).json()["role"] == "owner"


# RF-MEM-05-CA-01
def test_volver_a_agregar_a_quien_abandono(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    assert leave(client, other_token, project["id"]).status_code == 204

    response = client.post(
        f"{PROJECTS_URL}/{project['id']}/members",
        json={"username": "otro_username", "role": "viewer"},
        headers=bearer(access_token),
    )

    assert response.status_code == 201
    assert get_project(client, other_token, project["id"]).json()["role"] == "viewer"


# RNF-SEC-03
def test_responder_no_encontrado_a_quien_no_es_miembro(client, other_token, project):
    assert leave(client, other_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, project):
    response = client.delete(f"{PROJECTS_URL}/{project['id']}/members/me")

    assert response.status_code == 401
