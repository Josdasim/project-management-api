import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.public import AccountStatus
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
    third_token,
)
from tests.modules.tasks.conftest import new_task, project, set_status


def assign_task(client, token, project_id, task_id, assigned_to):
    return client.patch(
        f"{PROJECTS_URL}/{project_id}/tasks/{task_id}/assignee",
        json={"assigned_to": assigned_to},
        headers=bearer(token),
    )


def stored_assignee(db, task_id):
    db.expire_all()
    return db.get(TaskModel, uuid.UUID(task_id)).assigned_to


# RF-TASK-05-CA-01 y CA-04
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.ADMIN])
def test_propietario_asigna_a_un_miembro_o_administrador(
    client, access_token, other_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "otro_username"
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-01 y CA-04
def test_administrador_asigna_una_tarea(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, other_token, project["id"], task["id"], "dana_01")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "dana_01"


# RF-TASK-05-CA-01 y CA-04
def test_reasignar_deja_un_solo_responsable(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = assign_task(client, access_token, project["id"], task["id"], "tercer_user")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "tercer_user"


# RF-TASK-05-CA-01
def test_asignar_sin_distinguir_mayusculas(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "OTRO_USERNAME")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "otro_username"


# RF-TASK-05-CA-01
@pytest.mark.parametrize("role", [ProjectRole.OWNER, ProjectRole.ADMIN])
def test_propietario_y_administrador_desasignan(
    client, access_token, other_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )
    token = access_token

    response = assign_task(client, token, project["id"], task["id"], None)

    assert response.status_code == 200
    assert response.json()["assigned_to"] is None
    assert stored_assignee(db, task["id"]) is None


# RF-TASK-05-CA-02
def test_miembro_se_asigna_una_tarea_sin_responsable(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "otro_username"


# RF-TASK-05-CA-02
def test_miembro_se_desasigna_de_una_tarea_suya(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = assign_task(client, other_token, project["id"], task["id"], None)

    assert response.status_code == 200
    assert response.json()["assigned_to"] is None
    assert stored_assignee(db, task["id"]) is None


# RF-TASK-05-CA-02
def test_miembro_que_ya_es_responsable_se_asigna_de_nuevo_sin_cambios(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "otro_username"


# RF-TASK-05-CA-02
def test_rechazar_al_miembro_asignarse_una_tarea_con_otro_responsable(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea", assigned_to="dana_01")

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 403
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-02
@pytest.mark.parametrize("target", ["dana_01", "tercer_user", "no_existe"])
def test_rechazar_al_miembro_asignar_a_otro_usuario(
    client, access_token, other_token, third_token, db, project, target
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, other_token, project["id"], task["id"], target)

    assert response.status_code == 403
    assert stored_assignee(db, task["id"]) is None


# RF-TASK-05-CA-02
def test_rechazar_al_miembro_desasignar_a_otro(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea", assigned_to="dana_01")

    response = assign_task(client, other_token, project["id"], task["id"], None)

    assert response.status_code == 403
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-02
def test_rechazar_al_miembro_desasignar_una_tarea_sin_responsable(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, other_token, project["id"], task["id"], None)

    assert response.status_code == 403


# RF-TASK-05-CA-05
@pytest.mark.parametrize("target", ["otro_username", None])
def test_rechazar_al_observador(client, access_token, other_token, db, project, target):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea", assigned_to="dana_01")

    response = assign_task(client, other_token, project["id"], task["id"], target)

    assert response.status_code == 403
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-03
def test_rechazar_como_responsable_a_un_observador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 422
    assert stored_assignee(db, task["id"]) is None


# RF-TASK-05-CA-03
def test_rechazar_como_responsable_a_quien_no_es_miembro(
    client, access_token, other_token, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 422


# RF-TASK-05-CA-03
def test_rechazar_como_responsable_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 422


# RF-TASK-05-CA-03
def test_rechazar_como_responsable_a_un_username_inexistente(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, access_token, project["id"], task["id"], "no_existe")

    assert response.status_code == 422


# RF-TASK-05-CA-03
def test_rechazar_como_responsable_a_una_cuenta_desactivada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    account = db.scalar(select(AccountModel).where(AccountModel.username == "otro_username"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 422


# RF-TASK-05-CA-06
@pytest.mark.parametrize("current", [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
@pytest.mark.parametrize("target", ["otro_username", None])
def test_rechazar_cambiar_el_responsable_de_una_tarea_completada_o_cancelada(
    client, access_token, other_token, db, project, current, target
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea", assigned_to="dana_01")
    set_status(db, task["id"], current)

    response = assign_task(client, access_token, project["id"], task["id"], target)

    assert response.status_code == 409
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-06
def test_rechazar_al_miembro_ajeno_con_403_aunque_la_tarea_este_completada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea", assigned_to="dana_01")
    set_status(db, task["id"], TaskStatus.COMPLETED)

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 403


# RF-TASK-05-CA-06
def test_asignar_una_tarea_reabierta(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], TaskStatus.COMPLETED)
    client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/status",
        json={"status": "in_progress"},
        headers=bearer(access_token),
    )

    response = assign_task(client, access_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 200


# RF-TASK-05-CA-01
def test_rechazar_un_cuerpo_sin_responsable(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/assignee",
        json={},
        headers=bearer(access_token),
    )

    assert response.status_code == 422


# RF-TASK-05-CA-01
def test_responder_no_encontrado_si_la_tarea_no_existe(client, access_token, project):
    response = assign_task(client, access_token, project["id"], uuid.uuid4(), "dana_01")

    assert response.status_code == 404


# RF-TASK-05-CA-01
def test_responder_no_encontrado_si_la_tarea_es_de_otro_proyecto(client, access_token, project):
    other_project = create(client, access_token, name="Otro Proyecto")
    task = new_task(client, access_token, other_project["id"], title="De otro proyecto")

    response = assign_task(client, access_token, project["id"], task["id"], "dana_01")

    assert response.status_code == 404


# RF-TASK-05-CA-01
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 404


# RF-TASK-05-CA-01
def test_responder_no_encontrado_a_un_miembro_retirado(
    client, access_token, other_token, db, project
):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER, left_at=datetime.now(UTC))

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 404


# RF-TASK-05-CA-01
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    stored = db.scalar(select(ProjectModel).where(ProjectModel.name == "Mi Proyecto"))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    response = assign_task(client, access_token, project["id"], task["id"], "dana_01")

    assert response.status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    task = new_task(client, access_token, project["id"], title="Mi tarea")

    response = client.patch(
        f"{PROJECTS_URL}/{project['id']}/tasks/{task['id']}/assignee",
        json={"assigned_to": "dana_01"},
    )

    assert response.status_code == 401


# RF-TASK-05-CA-06
def test_rechazar_al_miembro_desasignarse_de_una_tarea_suya_completada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(
        client, access_token, project["id"], title="Mi tarea", assigned_to="otro_username"
    )
    set_status(db, task["id"], TaskStatus.COMPLETED)

    response = assign_task(client, other_token, project["id"], task["id"], None)

    assert response.status_code == 409
    assert stored_assignee(db, task["id"]) is not None


# RF-TASK-05-CA-06 (TASK-05.12)
@pytest.mark.parametrize("current", [TaskStatus.COMPLETED, TaskStatus.CANCELLED])
def test_rechazar_al_observador_con_403_aunque_la_tarea_este_cerrada(
    client, access_token, other_token, db, project, current
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], current)

    response = assign_task(client, other_token, project["id"], task["id"], "otro_username")

    assert response.status_code == 403


# RF-TASK-05-CA-06 (TASK-05.12)
def test_rechazar_al_miembro_asignar_a_otro_con_403_aunque_la_tarea_este_cerrada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    task = new_task(client, access_token, project["id"], title="Mi tarea")
    set_status(db, task["id"], TaskStatus.CANCELLED)

    response = assign_task(client, other_token, project["id"], task["id"], "dana_01")

    assert response.status_code == 403
