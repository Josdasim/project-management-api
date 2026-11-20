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


def edit_task(client, token, project_id, task_id, data):
    return client.patch(
        f"{PROJECTS_URL}/{project_id}/tasks/{task_id}", json=data, headers=bearer(token)
    )


def stored_task(db, task_id):
    db.expire_all()
    return db.get(TaskModel, uuid.UUID(task_id))


NEW_DATA = {"title": "Nuevo título", "description": "Nueva descripción", "priority": "urgent"}


# RF-TASK-04-CA-01
def test_propietario_edita_cualquier_tarea(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Mi tarea")

    response = edit_task(client, access_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 200
    assert response.json()["title"] == "Nuevo título"
    assert response.json()["description"] == "Nueva descripción"
    assert response.json()["priority"] == "urgent"


# RF-TASK-04-CA-01
def test_administrador_edita_cualquier_tarea(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 200
    assert stored_task(db, task["id"]).title == "Nuevo título"


# RF-TASK-04-CA-01
def test_miembro_edita_una_tarea_que_creo(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Mi tarea")

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 200


# RF-TASK-04-CA-01
def test_miembro_edita_una_tarea_asignada_a_el(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 200


# RF-TASK-04-CA-01
def test_rechazar_al_miembro_una_tarea_ajena(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 403
    assert stored_task(db, task["id"]).title == "Mi tarea"


# RF-TASK-04-CA-01
def test_rechazar_al_observador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 403
    assert stored_task(db, task["id"]).title == "Mi tarea"


# RF-TASK-04-CA-03
@pytest.mark.parametrize(
    "data, field, expected",
    [
        ({"title": "Solo título"}, "title", "Solo título"),
        ({"description": "Solo descripción"}, "description", "Solo descripción"),
        ({"priority": "high"}, "priority", "high"),
    ],
)
def test_conservar_los_campos_no_enviados(client, access_token, project, data, field, expected):
    task = new_task(
        client,
        access_token,
        project["id"],
        title="Original",
        description="Detalle original",
        priority="medium",
    )

    body = edit_task(client, access_token, project["id"], task["id"], data).json()

    original = {"title": "Original", "description": "Detalle original", "priority": "medium"}
    for name in original:
        assert body[name] == (expected if name == field else original[name])


# RF-TASK-04-CA-03
def test_borrar_la_descripcion_con_nulo(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea", description="Detalle")

    response = edit_task(client, access_token, project["id"], task["id"], {"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["title"] == "Mi tarea"


# RF-TASK-04-CA-03
def test_aceptar_un_cuerpo_vacio_sin_cambios(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea", priority="high")

    response = edit_task(client, access_token, project["id"], task["id"], {})

    assert response.status_code == 200
    assert response.json()["title"] == "Mi tarea"
    assert response.json()["priority"] == "high"


# RF-TASK-04-CA-02
@pytest.mark.parametrize(
    "data",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "a" * 201},
        {"title": None},
        {"description": "a" * 5001},
        {"priority": "extrema"},
        {"priority": None},
    ],
)
def test_rechazar_datos_invalidos(client, access_token, db, project, data):
    task = new_task(client, access_token, project["id"], title="Mi tarea", description="Detalle")

    response = edit_task(client, access_token, project["id"], task["id"], data)

    assert response.status_code == 422
    assert stored_task(db, task["id"]).title == "Mi tarea"


# RF-TASK-04-CA-02
def test_aceptar_titulo_y_descripcion_en_el_limite(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(
        client,
        access_token,
        project["id"],
        task["id"],
        {"title": "a" * 200, "description": "b" * 5000},
    )

    assert response.status_code == 200


# RF-TASK-04-CA-04
@pytest.mark.parametrize(
    "data",
    [
        {"status": "completed"},
        {"assigned_to": "otro_username"},
        {"created_by": "otro_username"},
        {"project_id": str(uuid.uuid4())},
    ],
)
def test_rechazar_campos_que_no_se_editan_por_esta_via(client, access_token, db, project, data):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(client, access_token, project["id"], task["id"], data)

    assert response.status_code == 422
    stored = stored_task(db, task["id"])
    assert stored.status == TaskStatus.PENDING
    assert stored.assigned_to is None


# RF-TASK-04-CA-05
@pytest.mark.parametrize("current", [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
def test_rechazar_editar_una_tarea_completada_o_cancelada(
    client, access_token, db, project, current
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], current)

    response = edit_task(client, access_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 409
    assert stored_task(db, task["id"]).title == "Mi tarea"


# RF-TASK-04-CA-05
def test_rechazar_al_miembro_ajeno_con_403_aunque_la_tarea_este_completada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], TaskStatus.COMPLETED)

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 403


# RF-TASK-04-CA-05
def test_reabrir_una_tarea_completada_y_editarla(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], TaskStatus.COMPLETED)
    reopened = client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/status",
        json={"status": "in_progress"},
        headers=bearer(access_token),
    )

    response = edit_task(client, access_token, project["id"], task["id"], NEW_DATA)

    assert reopened.status_code == 200
    assert response.status_code == 200
    assert response.json()["title"] == "Nuevo título"


# RF-TASK-04-CA-01
def test_responder_no_encontrado_si_la_tarea_no_existe(client, access_token, project):
    response = edit_task(client, access_token, project["id"], uuid.uuid4(), NEW_DATA)

    assert response.status_code == 404


# RF-TASK-04-CA-01
def test_responder_no_encontrado_si_la_tarea_es_de_otro_proyecto(client, access_token, project):
    other_project = create(client, access_token, name="Otro Proyecto")
    task = new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = edit_task(client, access_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 404


# RF-TASK-04-CA-01
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 404


# RF-TASK-04-CA-01
def test_responder_no_encontrado_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 404


# RF-TASK-04-CA-01
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    response = edit_task(client, access_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.patch(f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}", json=NEW_DATA)

    assert response.status_code == 401


# RF-TASK-04-CA-05 (TASK-04.13)
@pytest.mark.parametrize("current", [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
def test_rechazar_al_observador_con_403_aunque_la_tarea_este_cerrada(
    client, access_token, other_token, db, project, current
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], current)

    response = edit_task(client, other_token, project["id"], task["id"], NEW_DATA)

    assert response.status_code == 403