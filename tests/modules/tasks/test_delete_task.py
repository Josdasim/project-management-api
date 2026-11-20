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


def delete_task(client, token, project_id, task_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}/tasks/{task_id}", headers=bearer(token))


def exists(db, task_id):
    db.expire_all()
    return db.get(TaskModel, uuid.UUID(task_id)) is not None


# RF-TASK-07-CA-01 y CA-03
def test_propietario_elimina_una_tarea(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = delete_task(client, access_token, project["id"], task["id"])
    after = client.get(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}", headers=bearer(access_token)
    )

    assert response.status_code == 204
    assert after.status_code == 404
    assert not exists(db, task["id"])


# RF-TASK-07-CA-01
def test_administrador_elimina_cualquier_tarea(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = delete_task(client, other_token, project["id"], task["id"])

    assert response.status_code == 204
    assert not exists(db, task["id"])


# RF-TASK-07-CA-01
@pytest.mark.parametrize("current", list(TaskStatus))
def test_eliminar_una_tarea_en_cualquier_estado(client, access_token, db, project, current):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], current)

    response = delete_task(client, access_token, project["id"], task["id"])

    assert response.status_code == 204
    assert not exists(db, task["id"])


# RF-TASK-07-CA-04
def test_rechazar_al_miembro_aunque_haya_creado_la_tarea(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Mi tarea")

    response = delete_task(client, other_token, project["id"], task["id"])

    assert response.status_code == 403
    assert exists(db, task["id"])


# RF-TASK-07-CA-04
def test_rechazar_al_observador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = delete_task(client, other_token, project["id"], task["id"])

    assert response.status_code == 403
    assert exists(db, task["id"])


# RF-TASK-07-CA-02
def test_responder_no_encontrado_si_la_tarea_no_existe(client, access_token, project):
    assert delete_task(client, access_token, project["id"], uuid.uuid4()).status_code == 404


# RF-TASK-07-CA-02
def test_responder_no_encontrado_si_la_tarea_ya_fue_eliminada(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    delete_task(client, access_token, project["id"], task["id"])

    assert delete_task(client, access_token, project["id"], task["id"]).status_code == 404


# RF-TASK-07-CA-02
def test_responder_no_encontrado_si_la_tarea_es_de_otro_proyecto(client, access_token, db, project):
    other_project = create(client, access_token, name="Otro Proyecto")
    task = new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = delete_task(client, access_token, project["id"], task["id"])

    assert response.status_code == 404
    assert exists(db, task["id"])


# RF-TASK-07-CA-01
def test_responder_no_encontrado_a_quien_no_es_miembro(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    assert delete_task(client, other_token, project["id"], task["id"]).status_code == 404
    assert exists(db, task["id"])


# RF-TASK-07-CA-01
def test_responder_no_encontrado_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN, left_at=datetime.now(UTC))

    assert delete_task(client, other_token, project["id"], task["id"]).status_code == 404


# RF-TASK-07-CA-01
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    assert delete_task(client, access_token, project["id"], task["id"]).status_code == 404
    assert exists(db, task["id"])


# RF-TASK-07-CA-03
def test_no_listar_la_tarea_eliminada_y_conservar_las_demas(client, access_token, project):
    deleted = new_task(client, access_token, project["id"], title="Se elimina")
    new_task(client, access_token, project["id"], title="Se queda")
    delete_task(client, access_token, project["id"], deleted["id"])

    response = client.get(f"{PROJECTS_URL}/{project['id']}/tasks", headers=bearer(access_token))

    assert [item["title"] for item in response.json()["items"]] == ["Se queda"]
    assert response.json()["total"] == 1


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.delete(f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}")

    assert response.status_code == 401
