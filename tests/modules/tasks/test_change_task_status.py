import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.tasks.domain.enums import TaskStatus
from src.modules.tasks.infrastructure.models import Task as TaskModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)
from tests.modules.tasks.conftest import new_task, project, set_status


def change_status(client, token, project_id, task_id, status):
    return client.patch(
        f"{PROJECTS_URL}/{project_id}/tasks/{task_id}/status",
        json={"status": status},
        headers=bearer(token),
    )


def stored_status(db, task_id):
    db.expire_all()
    return db.get(TaskModel, uuid.UUID(task_id)).status


ALLOWED = [
    (TaskStatus.PENDING, TaskStatus.IN_PROGRESS),
    (TaskStatus.PENDING, TaskStatus.CANCELLED),
    (TaskStatus.IN_PROGRESS, TaskStatus.PENDING),
    (TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED),
    (TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED),
    (TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS),
    (TaskStatus.CANCELLED, TaskStatus.PENDING),
]

NOT_ALLOWED = [
    (TaskStatus.PENDING, TaskStatus.COMPLETED),
    (TaskStatus.COMPLETED, TaskStatus.PENDING),
    (TaskStatus.COMPLETED, TaskStatus.CANCELLED),
    (TaskStatus.CANCELLED, TaskStatus.IN_PROGRESS),
    (TaskStatus.CANCELLED, TaskStatus.COMPLETED),
]


# RF-TASK-06-CA-03
@pytest.mark.parametrize("origin, target", ALLOWED)
def test_cambiar_estado_con_transicion_permitida(client, access_token, db, project, origin, target):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], origin)

    response = change_status(client, access_token, project["id"], task["id"], target)

    assert response.status_code == 200
    assert response.json()["status"] == target
    assert stored_status(db, task["id"]) == target


# RF-TASK-06-CA-03
@pytest.mark.parametrize("origin, target", NOT_ALLOWED)
def test_rechazar_transicion_no_permitida(client, access_token, db, project, origin, target):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], origin)

    response = change_status(client, access_token, project["id"], task["id"], target)

    assert response.status_code == 409
    assert stored_status(db, task["id"]) == origin


# RF-TASK-06-CA-03
@pytest.mark.parametrize("current", list(TaskStatus))
def test_rechazar_pasar_al_mismo_estado(client, access_token, db, project, current):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], current)

    response = change_status(client, access_token, project["id"], task["id"], current)

    assert response.status_code == 409
    assert stored_status(db, task["id"]) == current


# RF-TASK-06-CA-02
def test_propietario_cambia_el_estado_de_cualquier_tarea(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = change_status(client, access_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 200


# RF-TASK-06-CA-02
def test_administrador_cambia_el_estado_de_cualquier_tarea(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


# RF-TASK-06-CA-02
def test_miembro_cambia_el_estado_de_una_tarea_asignada_a_el(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 200
    assert stored_status(db, task["id"]) == TaskStatus.IN_PROGRESS


# RF-TASK-06-CA-02
def test_rechazar_al_miembro_una_tarea_que_creo_sin_estar_asignada(
    client, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 403
    assert stored_status(db, task["id"]) == TaskStatus.PENDING


# RF-TASK-06-CA-02
def test_rechazar_al_miembro_una_tarea_asignada_a_otro(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 403
    assert stored_status(db, task["id"]) == TaskStatus.PENDING


# RF-TASK-06-CA-04
def test_rechazar_al_observador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 403
    assert stored_status(db, task["id"]) == TaskStatus.PENDING


# RF-TASK-06-CA-04
def test_rechazar_al_observador_aunque_la_transicion_sea_invalida(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "completed")

    assert response.status_code == 403


# RF-TASK-06-CA-01
@pytest.mark.parametrize("status", ["hecho", "", "IN_PROGRESS", None])
def test_rechazar_estado_invalido(client, access_token, project, status):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, access_token, project["id"], task["id"], status)

    assert response.status_code == 422


# RF-TASK-06-CA-01
def test_rechazar_campos_desconocidos_en_el_cuerpo(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/status",
        json={"status": "in_progress", "assigned_to": "otro_username"},
        headers=bearer(access_token),
    )

    assert response.status_code == 422


# RF-TASK-06-CA-03
def test_completar_y_reabrir_una_tarea(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    steps = ["in_progress", "completed", "in_progress", "pending", "cancelled", "pending"]

    for status in steps:
        response = change_status(client, access_token, project["id"], task["id"], status)

        assert response.status_code == 200
        assert response.json()["status"] == status


# RF-TASK-06-DERIVADO
def test_conservar_el_resto_de_los_campos(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client,
        access_token,
        project["id"],
        title="Mi tarea",
        description="Detalle",
        priority="high",
        assigned_to="otro_username",
    )

    body = change_status(client, access_token, project["id"], task["id"], "in_progress").json()

    assert body["title"] == "Mi tarea"
    assert body["description"] == "Detalle"
    assert body["priority"] == "high"
    assert body["created_by"] == "dana_01"
    assert body["assigned_to"] == "otro_username"


# RF-TASK-06-CA-02
def test_responder_no_encontrado_si_la_tarea_no_existe(client, access_token, project):
    response = change_status(client, access_token, project["id"], uuid.uuid4(), "in_progress")

    assert response.status_code == 404


# RF-TASK-06-CA-02
def test_responder_no_encontrado_si_la_tarea_es_de_otro_proyecto(client, access_token, project):
    other_project = create(client, access_token, name="Otro Proyecto")
    task = new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = change_status(client, access_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 404


# RF-TASK-06-CA-02
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 404


# RF-TASK-06-CA-02
def test_responder_no_encontrado_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    response = change_status(client, other_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 404


# RF-TASK-06-CA-02
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    response = change_status(client, access_token, project["id"], task["id"], "in_progress")

    assert response.status_code == 404


# RF-TASK-06-DERIVADO
def test_rechazar_un_id_que_no_es_uuid(client, access_token, project):
    response = change_status(client, access_token, project["id"], "no-es-un-uuid", "in_progress")

    assert response.status_code == 422


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 401


# RF-TASK-06-CA-02 y CA-03 (TASK-06.12)
@pytest.mark.parametrize("target", [TaskStatus.COMPLETED, TaskStatus.PENDING])
def test_rechazar_al_miembro_sin_la_tarea_con_403_aunque_la_transicion_sea_invalida(
    client, access_token, other_token, db, project, target
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Mi tarea")

    response = change_status(client, other_token, project["id"], task["id"], target)

    assert response.status_code == 403
