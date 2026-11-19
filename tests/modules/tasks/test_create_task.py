from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.public import AccountStatus
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.tasks.infrastructure.models import Task as TaskModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
    project,
    third_token,
)


def create_task(client, token, project_id, data):
    return client.post(f"{PROJECTS_URL}/{project_id}/tasks", json=data, headers=bearer(token))


# RF-TASK-01-CA-01 y CA-02
def test_crear_tarea_solo_con_el_titulo(client, access_token, project):
    response = create_task(client, access_token, project["id"], {"title": "Mi tarea"})

    assert response.status_code == 201
    body = response.json()
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
    assert body["title"] == "Mi tarea"
    assert body["description"] is None
    assert body["status"] == "pending"
    assert body["priority"] == "low"
    assert body["created_by"] == "dana_01"
    assert body["assigned_to"] is None


# RF-TASK-01-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER])
def test_administrador_y_miembro_crean_tareas(client, access_token, other_token, db, project, role):
    add_member(db, "Mi Proyecto", "otro_username", role)

    response = create_task(client, other_token, project["id"], {"title": "Mi tarea"})

    assert response.status_code == 201
    assert response.json()["created_by"] == "otro_username"


# RF-TASK-01-CA-05
def test_rechazar_que_el_observador_cree_tareas(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER)

    response = create_task(client, other_token, project["id"], {"title": "Mi tarea"})

    assert response.status_code == 403
    assert db.scalars(select(TaskModel)).all() == []


# RF-TASK-01-CA-01
def test_crear_tarea_con_descripcion_y_prioridad(client, access_token, project):
    data = {"title": "Mi tarea", "description": "Detalle", "priority": "urgent"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 201
    assert response.json()["description"] == "Detalle"
    assert response.json()["priority"] == "urgent"


# RF-TASK-01-CA-05
@pytest.mark.parametrize(
    "extra",
    [
        {"priority": "extreme"},
        {"priority": None},
        {"status": "completed"},
        {"created_by": "dana_01"},
        {"project_id": "x"},
    ],
)
def test_rechazar_datos_invalidos_y_campos_protegidos(client, access_token, project, extra):
    response = create_task(client, access_token, project["id"], {"title": "Mi tarea", **extra})

    assert response.status_code == 422


# RF-TASK-01-CA-05
@pytest.mark.parametrize("title", ["", "   ", "a" * 201])
def test_rechazar_titulo_invalido(client, access_token, project, title):
    response = create_task(client, access_token, project["id"], {"title": title})

    assert response.status_code == 422


# RF-TASK-01-CA-05
def test_rechazar_peticion_sin_titulo(client, access_token, project):
    assert create_task(client, access_token, project["id"], {}).status_code == 422


# RF-TASK-01-CA-05
def test_aceptar_titulo_de_200_caracteres(client, access_token, project):
    response = create_task(client, access_token, project["id"], {"title": "a" * 200})

    assert response.status_code == 201


# RF-TASK-01-CA-05
def test_rechazar_descripcion_de_5001_caracteres(client, access_token, project):
    data = {"title": "Mi tarea", "description": "a" * 5001}

    assert create_task(client, access_token, project["id"], data).status_code == 422


# RF-TASK-01-CA-05
def test_aceptar_descripcion_de_5000_caracteres(client, access_token, project):
    data = {"title": "Mi tarea", "description": "a" * 5000}

    assert create_task(client, access_token, project["id"], data).status_code == 201


# RF-TASK-01-CA-03 y CA-04
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.ADMIN])
def test_propietario_asigna_un_responsable(client, access_token, third_token, db, project, role):
    add_member(db, "Mi Proyecto", "tercer_user", role)
    data = {"title": "Mi tarea", "assigned_to": "tercer_user"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 201
    assert response.json()["assigned_to"] == "tercer_user"
    assert response.json()["created_by"] == "dana_01"


# RF-TASK-01-CA-03
def test_administrador_asigna_un_responsable(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    data = {"title": "Mi tarea", "assigned_to": "tercer_user"}

    response = create_task(client, other_token, project["id"], data)

    assert response.status_code == 201
    assert response.json()["assigned_to"] == "tercer_user"


# RF-TASK-01-CA-03
def test_asignar_un_responsable_sin_distinguir_mayusculas(
    client, access_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    data = {"title": "Mi tarea", "assigned_to": "TERCER_USER"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 201
    assert response.json()["assigned_to"] == "tercer_user"


# RF-TASK-01-CA-03
def test_miembro_se_asigna_a_si_mismo(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    data = {"title": "Mi tarea", "assigned_to": "otro_username"}

    response = create_task(client, other_token, project["id"], data)

    assert response.status_code == 201
    assert response.json()["assigned_to"] == "otro_username"


# RF-TASK-01-CA-03
@pytest.mark.parametrize("username", ["dana_01", "tercer_user", "no_existe"])
def test_rechazar_que_el_miembro_asigne_a_otro_usuario(
    client, access_token, other_token, third_token, db, project, username
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    data = {"title": "Mi tarea", "assigned_to": username}

    response = create_task(client, other_token, project["id"], data)

    assert response.status_code == 403
    assert db.scalars(select(TaskModel)).all() == []


# RF-TASK-01-CA-03
@pytest.mark.parametrize("username", ["tercer_user", "no_existe"])
def test_rechazar_responsable_que_no_es_miembro_o_no_existe(
    client, access_token, third_token, project, username
):
    data = {"title": "Mi tarea", "assigned_to": username}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 422


# RF-TASK-01-CA-03
def test_rechazar_responsable_observador(client, access_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.VIEWER)
    data = {"title": "Mi tarea", "assigned_to": "tercer_user"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 422


# RF-TASK-01-CA-03
def test_rechazar_responsable_retirado(client, access_token, third_token, db, project):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER, left_at=datetime.now(UTC))
    data = {"title": "Mi tarea", "assigned_to": "tercer_user"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 422


# RF-TASK-01-CA-03
def test_rechazar_responsable_con_cuenta_desactivada(
    client, access_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)
    account = db.scalar(select(AccountModel).where(AccountModel.username == "tercer_user"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()
    data = {"title": "Mi tarea", "assigned_to": "tercer_user"}

    response = create_task(client, access_token, project["id"], data)

    assert response.status_code == 422


# RF-TASK-01-CA-05
def test_responder_no_encontrado_a_quien_no_es_miembro(client, other_token, project):
    response = create_task(client, other_token, project["id"], {"title": "Mi tarea"})

    assert response.status_code == 404


# RF-TASK-01-CA-05
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db, project):
    stored = db.scalar(select(ProjectModel))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    response = create_task(client, access_token, project["id"], {"title": "Mi tarea"})

    assert response.status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, project):
    response = client.post(f"{PROJECTS_URL}/{project['id']}/tasks", json={"title": "Mi tarea"})

    assert response.status_code == 401
