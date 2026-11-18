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
    project,
    third_token,
)


def change(client, token, project_id, username, **data):
    return client.patch(
        f"{PROJECTS_URL}/{project_id}/members/{username}", json=data, headers=bearer(token)
    )


# RF-MEM-03-CA-01
def test_cambiar_rol_sin_distinguir_mayusculas(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = change(client, access_token, project["id"], "OTRO_USERNAME", role="viewer")

    assert response.status_code == 200
    assert response.json()["username"] == "otro_username"


# RF-MEM-03-CA-01
def test_propietario_cambia_entre_miembro_y_observador(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    to_viewer = change(client, access_token, project["id"], "otro_username", role="viewer")
    to_member = change(client, access_token, project["id"], "otro_username", role="member")

    assert to_viewer.status_code == 200
    assert to_viewer.json()["username"] == "otro_username"
    assert to_viewer.json()["role"] == "viewer"
    assert to_member.status_code == 200
    assert to_member.json()["role"] == "member"
    assert get_project(client, other_token, project["id"]).json()["role"] == "member"


# RF-MEM-03-CA-01
def test_administrador_cambia_entre_miembro_y_observador(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    to_viewer = change(client, other_token, project["id"], "tercer_user", role="viewer")
    to_member = change(client, other_token, project["id"], "tercer_user", role="member")

    assert to_viewer.status_code == 200
    assert to_viewer.json()["role"] == "viewer"
    assert to_member.status_code == 200
    assert to_member.json()["role"] == "member"


# RF-MEM-03-CA-02
def test_propietario_promueve_un_miembro_a_administrador(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = change(client, access_token, project["id"], "otro_username", role="admin")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert get_project(client, other_token, project["id"]).json()["role"] == "admin"


# RF-MEM-03-CA-02
def test_propietario_degrada_a_un_administrador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = change(client, access_token, project["id"], "otro_username", role="member")

    assert response.status_code == 200
    assert response.json()["role"] == "member"
    assert get_project(client, other_token, project["id"]).json()["role"] == "member"


# RF-MEM-03-CA-02
def test_rechazar_que_el_administrador_promueva_a_administrador(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    response = change(client, other_token, project["id"], "tercer_user", role="admin")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).json()["role"] == "member"


# RF-MEM-03-CA-03
def test_rechazar_que_el_administrador_cambie_a_otro_administrador(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.ADMIN)

    response = change(client, other_token, project["id"], "tercer_user", role="member")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).json()["role"] == "admin"


# RF-MEM-03-CA-03
@pytest.mark.parametrize("role", ["member", "viewer"])
def test_rechazar_que_el_administrador_cambie_su_propio_rol(
    client, access_token, other_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = change(client, other_token, project["id"], "otro_username", role=role)

    assert response.status_code == 403
    assert get_project(client, other_token, project["id"]).json()["role"] == "admin"


# RF-MEM-03-CA-04
@pytest.mark.parametrize("role", ["admin", "member", "viewer"])
def test_rechazar_que_el_propietario_cambie_su_propio_rol(client, access_token, project, role):
    response = change(client, access_token, project["id"], "dana_01", role=role)

    assert response.status_code == 403
    assert get_project(client, access_token, project["id"]).json()["role"] == "owner"


# RF-MEM-03-CA-04
def test_rechazar_que_el_administrador_cambie_el_rol_del_propietario(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = change(client, other_token, project["id"], "dana_01", role="member")

    assert response.status_code == 403
    assert get_project(client, access_token, project["id"]).json()["role"] == "owner"


# RF-MEM-03-CA-04
def test_rechazar_asignar_el_rol_propietario(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = change(client, access_token, project["id"], "otro_username", role="owner")

    assert response.status_code == 422
    assert get_project(client, other_token, project["id"]).json()["role"] == "member"


# RNF-SEC-03
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_rechazar_que_miembro_u_observador_cambien_roles(
    client, access_token, other_token, third_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    response = change(client, other_token, project["id"], "tercer_user", role="viewer")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).json()["role"] == "member"


# RF-MEM-03-CA-01
@pytest.mark.parametrize("username", ["tercer_user", "no_existe"])
def test_responder_no_encontrado_si_no_es_miembro(
    client, access_token, third_token, project, username
):
    response = change(client, access_token, project["id"], username, role="member")

    assert response.status_code == 404


# RF-MEM-03-CA-01
def test_responder_no_encontrado_si_el_miembro_fue_retirado(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    response = change(client, access_token, project["id"], "otro_username", role="viewer")

    assert response.status_code == 404


# RF-MEM-03-CA-01
@pytest.mark.parametrize(
    "data",
    [
        {"role": "superman"},
        {"role": None},
        {},
        {"role": "member", "user_id": "x"},
    ],
)
def test_rechazar_datos_invalidos(client, access_token, other_token, db, project, data):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)

    response = change(client, access_token, project["id"], "otro_username", **data)

    assert response.status_code == 422
    assert get_project(client, other_token, project["id"]).json()["role"] == "viewer"


# RNF-SEC-03
def test_responder_no_encontrado_a_quien_no_es_miembro_del_proyecto(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    response = change(client, other_token, project["id"], "tercer_user", role="viewer")

    assert response.status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = client.patch(
        f"{PROJECTS_URL}/{project['id']}/members/otro_username", json={"role": "viewer"}
    )

    assert response.status_code == 401
