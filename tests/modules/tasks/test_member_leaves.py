import uuid

import pytest

from src.modules.projects.domain.enums import ProjectRole
from src.modules.tasks.domain.enums import TaskStatus
from src.modules.tasks.infrastructure.models import Task as TaskModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    other_token,
)
from tests.modules.tasks.conftest import new_task, project, set_status


def get_task(client, token, project_id, task_id):
    return client.get(f"{PROJECTS_URL}/{project_id}/tasks/{task_id}", headers=bearer(token))


def remove_member(client, token, project_id, username):
    return client.delete(f"{PROJECTS_URL}/{project_id}/members/{username}", headers=bearer(token))


def leave_project(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}/members/me", headers=bearer(token))


def assigned_tasks(client, access_token, project, other_token, db):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    tasks = {
        status: new_task(
            client,
            access_token,
            project["id"],
            title=f"Tarea {status}",
            assigned_to="otro_username",
        )
        for status in TaskStatus
    }
    for status, task in tasks.items():
        set_status(db, task["id"], status)
    return tasks


# MEM-04.7 y MOD-02
def test_desasignar_las_tareas_en_cualquier_estado_al_retirar_a_un_miembro(
    client, access_token, other_token, db, project
):
    tasks = assigned_tasks(client, access_token, project, other_token, db)
    kept = new_task(
        client, access_token, project["id"], title="Del propietario", assigned_to="dana_01"
    )

    response = remove_member(client, access_token, project["id"], "otro_username")

    assert response.status_code == 204
    for task in tasks.values():
        body = get_task(client, access_token, project["id"], task["id"]).json()
        assert body["assigned_to"] is None
    assert (
        get_task(client, access_token, project["id"], kept["id"]).json()["assigned_to"] == "dana_01"
    )


# MEM-05.3 y MOD-02
def test_desasignar_las_tareas_en_cualquier_estado_al_abandonar_el_proyecto(
    client, access_token, other_token, db, project
):
    tasks = assigned_tasks(client, access_token, project, other_token, db)
    kept = new_task(
        client, access_token, project["id"], title="Del propietario", assigned_to="dana_01"
    )

    response = leave_project(client, other_token, project["id"])

    assert response.status_code == 204
    for task in tasks.values():
        body = get_task(client, access_token, project["id"], task["id"]).json()
        assert body["assigned_to"] is None
    assert (
        get_task(client, access_token, project["id"], kept["id"]).json()["assigned_to"] == "dana_01"
    )


# MOD-02
def test_conservar_el_estado_y_el_resto_de_los_campos_de_las_tareas_desasignadas(
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
    set_status(db, task["id"], TaskStatus.IN_PROGRESS)

    leave_project(client, other_token, project["id"])
    body = get_task(client, access_token, project["id"], task["id"]).json()

    assert body["assigned_to"] is None
    assert body["status"] == "in_progress"
    assert body["title"] == "Mi tarea"
    assert body["description"] == "Detalle"
    assert body["priority"] == "high"


# MOD-02
def test_no_desasignar_las_tareas_de_otro_proyecto(client, access_token, other_token, db, project):
    from tests.modules.projects.conftest import create

    other_project = create(client, access_token, name="Otro Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Otro Proyecto", "otro_username", ProjectRole.MEMBER)
    elsewhere = new_task(
        client, access_token, other_project["id"], title="Otro", assigned_to="otro_username"
    )

    leave_project(client, other_token, project["id"])
    body = get_task(client, access_token, other_project["id"], elsewhere["id"]).json()

    assert body["assigned_to"] == "otro_username"


# MOD-03
@pytest.mark.parametrize("how", ["retirar", "abandonar"])
def test_conservar_la_tarea_y_su_creador_cuando_el_creador_sale(
    client, access_token, other_token, db, project, how
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, other_token, project["id"], title="Creada por otro")

    if how == "retirar":
        remove_member(client, access_token, project["id"], "otro_username")
    else:
        leave_project(client, other_token, project["id"])
    response = get_task(client, access_token, project["id"], task["id"])

    assert response.status_code == 200
    assert response.json()["created_by"] == "otro_username"
    assert response.json()["title"] == "Creada por otro"


# MEM-04.7
def test_desasignar_solo_si_la_salida_se_completa(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = remove_member(client, other_token, project["id"], "dana_01")
    stored = db.get(TaskModel, uuid.UUID(task["id"]))
    db.refresh(stored)

    assert response.status_code == 403
    assert stored.assigned_to is not None
