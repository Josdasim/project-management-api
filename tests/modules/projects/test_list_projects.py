from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from tests.modules.projects.conftest import PROJECTS_URL, access_token, bearer, create, other_token


def list_projects(client, token, **params):
    return client.get(PROJECTS_URL, params=params, headers=bearer(token))


def names(response):
    return {item["name"] for item in response.json()["items"]}


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


# RF-PROJ-02-CA-01
def test_listar_solo_los_proyectos_donde_es_miembro(client, access_token, other_token):
    create(client, access_token, name="Mio 1")
    create(client, access_token, name="Mio 2")
    create(client, other_token, name="Ajeno")

    response = list_projects(client, access_token)

    assert response.status_code == 200
    assert names(response) == {"Mio 1", "Mio 2"}
    assert response.json()["total"] == 2


# RF-PROJ-02-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_listar_proyectos_donde_es_miembro_con_cualquier_rol(
    client, access_token, other_token, db, role
):
    create(client, other_token, name="Compartido")
    add_member(db, "Compartido", "dana_01", role)

    items = list_projects(client, access_token).json()["items"]

    assert [(item["name"], item["role"]) for item in items] == [("Compartido", role.value)]


# RF-PROJ-02-CA-01
def test_no_listar_proyectos_con_membresia_finalizada(client, access_token, other_token, db):
    create(client, other_token, name="Finalizado")
    add_member(db, "Finalizado", "dana_01", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert names(list_projects(client, access_token)) == set()


# RF-PROJ-02-CA-02
def test_no_listar_proyectos_eliminados_logicamente(client, access_token, db):
    create(client, access_token, name="Mi Proyecto")
    project = db.scalar(select(ProjectModel))
    project.deleted_at = datetime.now(UTC)
    db.commit()

    assert names(list_projects(client, access_token)) == set()


# RF-PROJ-02-CA-03
def test_paginar_el_listado(client, access_token):
    for name in ("P1", "P2", "P3"):
        create(client, access_token, name=name)

    first = list_projects(client, access_token, page=1, page_size=2).json()
    second = list_projects(client, access_token, page=2, page_size=2).json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert first["total"] == second["total"] == 3
    assert (first["page"], second["page"], first["page_size"]) == (1, 2, 2)


# RF-PROJ-02-CA-03
def test_usar_valores_por_defecto_de_paginacion(client, access_token):
    body = list_projects(client, access_token).json()

    assert (body["page"], body["page_size"]) == (1, 20)


# RF-PROJ-02-CA-03
@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
def test_rechazar_parametros_de_paginacion_invalidos(client, access_token, params):
    assert list_projects(client, access_token, **params).status_code == 422


# RF-PROJ-02-CA-04
@pytest.mark.parametrize("search", ["alfa", "ALFA"])
def test_buscar_por_nombre_sin_distinguir_mayusculas(client, access_token, search):
    for name in ("Alfa Uno", "ALFA dos", "Beta"):
        create(client, access_token, name=name)

    response = list_projects(client, access_token, search=search)

    assert names(response) == {"Alfa Uno", "ALFA dos"}
    assert response.json()["total"] == 2


# RF-PROJ-02-CA-04
def test_buscar_solo_entre_los_proyectos_propios(client, access_token, other_token):
    create(client, access_token, name="Alfa Mio")
    create(client, other_token, name="Alfa Ajeno")

    assert names(list_projects(client, access_token, search="alfa")) == {"Alfa Mio"}


# RF-PROJ-02-DERIVADO
def test_devolver_el_id_y_los_datos_de_cada_proyecto(client, access_token):
    create(client, access_token, name="Mi Proyecto", description="Descripción")

    item = list_projects(client, access_token).json()["items"][0]

    assert set(item) == {"id", "name", "description", "status", "created_at", "role"}
    assert item["role"] == "owner"


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(PROJECTS_URL).status_code == 401
