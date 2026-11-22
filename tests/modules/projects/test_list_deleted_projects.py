import pytest

from src.modules.projects.domain.enums import ProjectRole
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)

DELETED_URL = f"{PROJECTS_URL}/deleted"


def delete_project(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


def list_deleted(client, token, **params):
    return client.get(DELETED_URL, params=params, headers=bearer(token))


def names(response):
    return [item["name"] for item in response.json()["items"]]


# RF-PROJ-06-CA-01
def test_listar_los_proyectos_eliminados_del_propietario(client, access_token):
    first = create(client, access_token, name="Primero")
    second = create(client, access_token, name="Segundo")
    delete_project(client, access_token, first["id"])
    delete_project(client, access_token, second["id"])

    response = list_deleted(client, access_token)

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert sorted(names(response)) == ["Primero", "Segundo"]


# RF-PROJ-06-CA-01
def test_devolver_los_campos_del_proyecto_y_la_fecha_de_eliminacion(client, access_token):
    project = create(client, access_token, name="Mi Proyecto", description="Detalle")
    delete_project(client, access_token, project["id"])

    item = list_deleted(client, access_token).json()["items"][0]

    assert item["id"] == project["id"]
    assert item["name"] == "Mi Proyecto"
    assert item["description"] == "Detalle"
    assert item["status"] == "active"
    assert item["deleted_at"] is not None
    assert "owner_id" not in item


# RF-PROJ-06-CA-01
def test_no_listar_un_proyecto_eliminado_donde_solo_es_administrador(
    client, access_token, other_token, db
):
    foreign = create(client, other_token, name="Ajeno")
    add_member(db, "Ajeno", "dana_01", ProjectRole.ADMIN)
    delete_project(client, other_token, foreign["id"])

    response = list_deleted(client, access_token)

    assert response.status_code == 200
    assert response.json()["items"] == []


# RF-PROJ-06-CA-01
def test_no_listar_los_proyectos_eliminados_de_otro_usuario(client, access_token, other_token):
    mine = create(client, access_token, name="Mio")
    theirs = create(client, other_token, name="Suyo")
    delete_project(client, access_token, mine["id"])
    delete_project(client, other_token, theirs["id"])

    assert names(list_deleted(client, access_token)) == ["Mio"]
    assert names(list_deleted(client, other_token)) == ["Suyo"]


# RF-PROJ-06-CA-01
def test_no_listar_los_proyectos_activos(client, access_token):
    create(client, access_token, name="Activo")
    gone = create(client, access_token, name="Eliminado")
    delete_project(client, access_token, gone["id"])

    assert names(list_deleted(client, access_token)) == ["Eliminado"]


# RF-PROJ-06-CA-02
def test_paginar_los_proyectos_eliminados(client, access_token):
    for number in range(21):
        project = create(client, access_token, name=f"Proyecto {number}")
        delete_project(client, access_token, project["id"])

    first = list_deleted(client, access_token).json()
    second = list_deleted(client, access_token, page=2).json()

    assert len(first["items"]) == 20
    assert first["total"] == 21
    assert first["page_size"] == 20
    assert len(second["items"]) == 1


# RF-PROJ-06
def test_ordenar_del_eliminado_mas_recientemente_al_mas_antiguo(client, access_token):
    for name in ["A", "B", "C"]:
        project = create(client, access_token, name=name)
        delete_project(client, access_token, project["id"])

    assert names(list_deleted(client, access_token)) == ["C", "B", "A"]


# RF-PROJ-06
@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_rechazar_paginacion_invalida(client, access_token, params):
    assert list_deleted(client, access_token, **params).status_code == 422


# RF-PROJ-06
def test_no_interpretar_deleted_como_un_id(client, access_token):
    response = list_deleted(client, access_token)

    assert response.status_code == 200


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(DELETED_URL).status_code == 401
