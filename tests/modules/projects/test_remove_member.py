from datetime import UTC, datetime

import pytest

from src.modules.projects.domain.enums import ProjectRole
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    get_project,
    other_token,
    third_token,
)


def remove(client, token, project_id, username):
    return client.delete(f"{PROJECTS_URL}/{project_id}/members/{username}", headers=bearer(token))


# RF-MEM-04-CA-01 y CA-02
def test_propietario_retira_a_un_miembro(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = remove(client, access_token, project["id"], "otro_username")

    assert response.status_code == 204
    listing = client.get(f"{PROJECTS_URL}/{project['id']}/members", headers=bearer(access_token))
    assert [item["username"] for item in listing.json()["items"]] == ["dana_01"]


# RF-MEM-04-CA-02
def test_devolver_no_encontrado_al_retirado_que_consulta_el_proyecto(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    assert get_project(client, other_token, project["id"]).status_code == 200

    assert remove(client, access_token, project["id"], "otro_username").status_code == 204

    assert get_project(client, other_token, project["id"]).status_code == 404


# RF-MEM-04-CA-01
def test_propietario_retira_a_un_administrador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    assert remove(client, access_token, project["id"], "otro_username").status_code == 204


# RF-MEM-04-CA-01
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_administrador_retira_a_miembro_y_observador(
    client, access_token, other_token, third_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", role)

    response = remove(client, other_token, project["id"], "tercer_user")

    assert response.status_code == 204
    assert get_project(client, third_token, project["id"]).status_code == 404


# RF-MEM-04-CA-01
def test_rechazar_que_el_administrador_retire_a_otro_administrador(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.ADMIN)

    response = remove(client, other_token, project["id"], "tercer_user")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).status_code == 200


# RF-MEM-04-CA-01
def test_rechazar_que_el_administrador_retire_al_propietario(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = remove(client, other_token, project["id"], "dana_01")

    assert response.status_code == 403
    assert get_project(client, access_token, project["id"]).status_code == 200


# RF-MEM-04-CA-01
def test_rechazar_que_el_propietario_se_retire_a_si_mismo(client, access_token, project):
    response = remove(client, access_token, project["id"], "dana_01")

    assert response.status_code == 403
    assert get_project(client, access_token, project["id"]).json()["role"] == "owner"


# RF-MEM-04-CA-01
def test_rechazar_que_el_administrador_se_retire_a_si_mismo(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = remove(client, other_token, project["id"], "otro_username")

    assert response.status_code == 403
    assert get_project(client, other_token, project["id"]).status_code == 200


# RNF-SEC-03
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_rechazar_que_miembro_u_observador_retiren(
    client, access_token, other_token, third_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    response = remove(client, other_token, project["id"], "tercer_user")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).status_code == 200


# RF-MEM-04-CA-01
@pytest.mark.parametrize("username", ["tercer_user", "no_existe"])
def test_responder_no_encontrado_si_no_es_miembro(
    client, access_token, third_token, project, username
):
    assert remove(client, access_token, project["id"], username).status_code == 404


# RF-MEM-04-CA-01
def test_responder_no_encontrado_si_ya_fue_retirado(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert remove(client, access_token, project["id"], "otro_username").status_code == 404


# RF-MEM-04-CA-01
def test_retirar_sin_distinguir_mayusculas(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    assert remove(client, access_token, project["id"], "OTRO_USERNAME").status_code == 204


# RNF-SEC-03
def test_responder_no_encontrado_a_quien_no_es_miembro_del_proyecto(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    assert remove(client, other_token, project["id"], "tercer_user").status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = client.delete(f"{PROJECTS_URL}/{project['id']}/members/otro_username")

    assert response.status_code == 401
