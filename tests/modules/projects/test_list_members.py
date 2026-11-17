from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    REGISTER_URL,
    USER,
    access_token,
    bearer,
    login_token,
    other_token,
    add_member,
    project
)

USERS_ME_URL = "/api/v1/users/me"


def members(client, token, project_id, **params):
    return client.get(f"{PROJECTS_URL}/{project_id}/members", params=params, headers=bearer(token))


@pytest.fixture
def third_token(client):
    data = {
        **USER,
        "username": "tercer_user",
        "email": "tercer@correo.com",
        "first_name": "Carlos",
    }
    assert client.post(REGISTER_URL, json=data).status_code == 201
    token = login_token(client, "tercer_user")
    response = client.patch(USERS_ME_URL, json={"last_name": "Rojas"}, headers=bearer(token))
    assert response.status_code == 200
    return token


# RF-MEM-02-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_listar_miembros_con_cualquier_rol(client, other_token, db, project, role):
    add_member(db, "Mi Proyecto", "otro_username", role)

    response = members(client, other_token, project["id"])

    assert response.status_code == 200
    usernames = [item["username"] for item in response.json()["items"]]
    assert usernames == ["dana_01", "otro_username"]


# RF-MEM-02-CA-01
def test_no_listar_miembros_retirados(client, access_token, other_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    body = members(client, access_token, project["id"]).json()

    assert body["total"] == 2
    assert "tercer_user" not in [item["username"] for item in body["items"]]


# RF-MEM-02-CA-02
def test_devolver_solo_datos_publicos(client, access_token, project):
    response = members(client, access_token, project["id"])

    item = response.json()["items"][0]
    assert set(item) == {"username", "first_name", "last_name", "role", "joined_at"}
    assert item["username"] == "dana_01"
    assert item["first_name"] == "Dana"
    assert item["role"] == "owner"


# RF-MEM-02-CA-03
@pytest.mark.parametrize("search", ["TERC", "carl", "ROJAS", "carlos roj"])
def test_buscar_miembros_de_forma_parcial(
    client, access_token, other_token, third_token, db, project, search
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    body = members(client, access_token, project["id"], search=search).json()

    assert [item["username"] for item in body["items"]] == ["tercer_user"]


# RF-MEM-02-CA-03
def test_devolver_lista_vacia_si_nadie_coincide(client, access_token, project):
    body = members(client, access_token, project["id"], search="zzz").json()

    assert body["items"] == []
    assert body["total"] == 0


# RF-MEM-02-CA-03
def test_filtrar_miembros_por_rol(client, access_token, other_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    body = members(client, access_token, project["id"], role="admin").json()

    assert [item["username"] for item in body["items"]] == ["otro_username"]


# RF-MEM-02-CA-03
def test_combinar_busqueda_y_rol(client, access_token, other_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.ADMIN)

    body = members(client, access_token, project["id"], search="dana", role="admin").json()

    assert [item["username"] for item in body["items"]] == ["otro_username"]


# RF-MEM-02-DERIVADO
def test_paginar_miembros(client, access_token, other_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    first = members(client, access_token, project["id"], page=1, page_size=2).json()
    second = members(client, access_token, project["id"], page=2, page_size=2).json()

    assert first["total"] == 3
    assert first["page_size"] == 2
    assert [item["username"] for item in first["items"]] == ["dana_01", "otro_username"]
    assert [item["username"] for item in second["items"]] == ["tercer_user"]


# RF-MEM-02-DERIVADO
def test_rechazar_tamano_de_pagina_invalido(client, access_token, project):
    assert members(client, access_token, project["id"], page_size=0).status_code == 422


# RNF-SEC-03
def test_responder_no_encontrado_a_quien_no_es_miembro(client, other_token, project):
    assert members(client, other_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_responder_no_encontrado_a_un_miembro_retirado(client, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert members(client, other_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, project):
    response = client.get(f"{PROJECTS_URL}/{project['id']}/members")

    assert response.status_code == 401
