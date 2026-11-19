import uuid
from datetime import UTC, datetime

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
from tests.modules.tasks.conftest import new_task, project


def get_task(client, token, project_id, task_id):
    return client.get(f"{PROJECTS_URL}/{project_id}/tasks/{task_id}", headers=bearer(token))


# RF-TASK-03-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_consultar_tarea_con_cualquier_rol(client, access_token, other_token, db, project, role):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", role)

    response = get_task(client, other_token, project["id"], task["id"])

    assert response.status_code == 200
    assert response.json()["title"] == "Mi tarea"


# RF-TASK-03-CA-01
def test_propietario_consulta_la_tarea(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    assert get_task(client, access_token, project["id"], task["id"]).status_code == 200


# RF-TASK-03-CA-03
def test_devolver_creador_y_responsable_por_username(
    client, access_token, other_token, db, project
):
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

    body = get_task(client, access_token, project["id"], task["id"]).json()

    assert set(body) == {
        "id",
        "title",
        "description",
        "status",
        "priority",
        "created_by",
        "assigned_to",
        "created_at",
        "updated_at",
    }
    assert body["id"] == task["id"]
    assert body["created_by"] == "dana_01"
    assert body["assigned_to"] == "otro_username"
    assert body["status"] == "pending"
    assert body["priority"] == "high"


# RF-TASK-03-CA-03
def test_devolver_responsable_nulo_si_no_tiene(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    body = get_task(client, access_token, project["id"], task["id"]).json()

    assert body["assigned_to"] is None


# RF-TASK-03-CA-02
def test_responder_no_encontrado_si_la_tarea_no_existe(client, access_token, project):
    response = get_task(client, access_token, project["id"], uuid.uuid4())

    assert response.status_code == 404


# RF-TASK-03-CA-02
def test_responder_no_encontrado_si_la_tarea_es_de_otro_proyecto(client, access_token, project):
    other_project = create(client, access_token, name="Otro Proyecto")
    task = new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = get_task(client, access_token, project["id"], task["id"])

    assert response.status_code == 404


# RF-TASK-03-CA-02
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    assert get_task(client, other_token, project["id"], task["id"]).status_code == 404


# RF-TASK-03-CA-02
def test_responder_no_encontrado_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    assert get_task(client, other_token, project["id"], task["id"]).status_code == 404


# RF-TASK-03-CA-02
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    assert get_task(client, access_token, project["id"], task["id"]).status_code == 404


# RF-TASK-03-DERIVADO
def test_rechazar_un_id_que_no_es_uuid(client, access_token, project):
    assert get_task(client, access_token, project["id"], "no-es-un-uuid").status_code == 422


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.get(f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}")

    assert response.status_code == 401
