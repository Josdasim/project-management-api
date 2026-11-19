import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.tasks.domain.enums import TaskStatus
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)
from tests.modules.tasks.conftest import new_task, project, set_status


def list_tasks(client, token, project_id, **params):
    return client.get(f"{PROJECTS_URL}/{project_id}/tasks", params=params, headers=bearer(token))


def titles(response):
    return [item["title"] for item in response.json()["items"]]


# RF-TASK-02-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_listar_tareas_con_cualquier_rol(client, access_token, other_token, db, project, role):
    add_member(db, "Mi Proyecto", "otro_username", role)
    other_project = create(client, access_token, name="Otro Proyecto")
    new_task(client, access_token, project["id"], title="De este proyecto")
    new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = list_tasks(client, other_token, project["id"])

    assert response.status_code == 200
    assert titles(response) == ["De este proyecto"]


# RF-TASK-02-CA-01
def test_listar_un_proyecto_sin_tareas(client, access_token, project):
    response = list_tasks(client, access_token, project["id"])

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


# RF-TASK-02-CA-02
def test_paginar_con_el_tamano_por_defecto(client, access_token, project):
    for number in range(21):
        new_task(client, access_token, project["id"], title=f"Tarea {number}")

    first = list_tasks(client, access_token, project["id"]).json()
    second = list_tasks(client, access_token, project["id"], page=2).json()

    assert len(first["items"]) == 20
    assert first["total"] == 21
    assert first["page_size"] == 20
    assert len(second["items"]) == 1


# RF-TASK-02-CA-03
def test_filtrar_por_estado(client, access_token, db, project):
    new_task(client, access_token, project["id"], title="Pendiente")
    started = new_task(client, access_token, project["id"], title="En curso")
    set_status(db, started["id"], TaskStatus.IN_PROGRESS)

    response = list_tasks(client, access_token, project["id"], status="in_progress")

    assert titles(response) == ["En curso"]


# RF-TASK-02-CA-03
def test_filtrar_por_prioridad(client, access_token, project):
    new_task(client, access_token, project["id"], title="Normal")
    new_task(client, access_token, project["id"], title="Urgente", priority="urgent")

    response = list_tasks(client, access_token, project["id"], priority="urgent")

    assert titles(response) == ["Urgente"]


# RF-TASK-02-CA-03
def test_filtrar_por_responsable(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    new_task(client, access_token, project["id"], title="Sin responsable")
    new_task(client, access_token, project["id"], title="Mia", assigned_to="otro_username")

    exact = list_tasks(client, access_token, project["id"], assigned_to="otro_username")
    upper = list_tasks(client, access_token, project["id"], assigned_to="OTRO_USERNAME")

    assert titles(exact) == ["Mia"]
    assert titles(upper) == ["Mia"]


# RF-TASK-02-CA-03
def test_devolver_lista_vacia_si_el_responsable_no_existe(client, access_token, project):
    new_task(client, access_token, project["id"], title="Una tarea")

    response = list_tasks(client, access_token, project["id"], assigned_to="no_existe")

    assert response.status_code == 200
    assert response.json()["items"] == []


# RF-TASK-02-CA-03
def test_combinar_filtros(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    new_task(
        client, access_token, project["id"], title="A", priority="high", assigned_to="otro_username"
    )
    started = new_task(
        client, access_token, project["id"], title="B", priority="high", assigned_to="otro_username"
    )
    new_task(client, access_token, project["id"], title="C", assigned_to="otro_username")
    new_task(client, access_token, project["id"], title="D", priority="high")
    set_status(db, started["id"], TaskStatus.IN_PROGRESS)

    response = list_tasks(
        client,
        access_token,
        project["id"],
        status="pending",
        priority="high",
        assigned_to="otro_username",
    )

    assert titles(response) == ["A"]


# RF-TASK-02-CA-04
@pytest.mark.parametrize(
    "search, expected",
    [
        ("INFORME", ["Revisar", "Escribir informe"]),
        ("final", ["Revisar"]),
        ("escribir", ["Escribir informe"]),
        ("zzz", []),
        ("%", []),
    ],
)
def test_buscar_por_titulo_y_descripcion(client, access_token, project, search, expected):
    new_task(client, access_token, project["id"], title="Escribir informe")
    new_task(client, access_token, project["id"], title="Revisar", description="Informe final")
    new_task(client, access_token, project["id"], title="Planear", description="Otra cosa")

    response = list_tasks(client, access_token, project["id"], search=search)

    assert titles(response) == expected


# RF-TASK-02-CA-03 y CA-04
def test_combinar_busqueda_y_filtros(client, access_token, project):
    new_task(client, access_token, project["id"], title="Escribir informe")
    new_task(client, access_token, project["id"], title="Revisar informe", priority="high")

    response = list_tasks(client, access_token, project["id"], search="informe", priority="high")

    assert titles(response) == ["Revisar informe"]


# RF-TASK-02-DERIVADO
def test_ordenar_de_la_mas_reciente_a_la_mas_antigua(client, access_token, project):
    for title in ["A", "B", "C"]:
        new_task(client, access_token, project["id"], title=title)

    first = list_tasks(client, access_token, project["id"], page_size=2)
    second = list_tasks(client, access_token, project["id"], page_size=2, page=2)

    assert titles(first) == ["C", "B"]
    assert titles(second) == ["A"]


# RF-TASK-02-CA-03
@pytest.mark.parametrize(
    "params",
    [{"status": "otra"}, {"priority": "extrema"}, {"page_size": 0}, {"page": 0}],
)
def test_rechazar_filtros_invalidos(client, access_token, project, params):
    assert list_tasks(client, access_token, project["id"], **params).status_code == 422


# RF-TASK-02-CA-05
def test_responder_no_encontrado_a_quien_no_es_miembro(client, other_token, project):
    assert list_tasks(client, other_token, project["id"]).status_code == 404


# RF-TASK-02-CA-05
def test_responder_no_encontrado_a_un_miembro_retirado(client, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert list_tasks(client, other_token, project["id"]).status_code == 404


# RF-TASK-02-CA-05
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    assert list_tasks(client, access_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, project):
    response = client.get(f"{PROJECTS_URL}/{project['id']}/tasks")

    assert response.status_code == 401
