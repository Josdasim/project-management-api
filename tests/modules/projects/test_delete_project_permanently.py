import uuid

import pytest
from sqlalchemy import func, select

from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from src.modules.tasks.infrastructure.models import Task as TaskModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    USER,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)
from tests.modules.tasks.conftest import new_task


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")


def delete_project(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


def permanent(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}/permanent", headers=bearer(token))


def count(db, model, project_id):
    db.expire_all()
    column = model.id if model is ProjectModel else model.project_id
    return db.scalar(select(func.count()).select_from(model).where(column == uuid.UUID(project_id)))


def trashed(client, access_token, project):
    delete_project(client, access_token, project["id"])
    return project


# RF-PROJ-10-CA-01
def test_eliminar_permanentemente_un_proyecto_eliminado(client, access_token, db, project):
    trashed(client, access_token, project)

    response = permanent(client, access_token, project["id"])

    assert response.status_code == 204
    assert response.content == b""
    assert count(db, ProjectModel, project["id"]) == 0


# RF-PROJ-10-CA-01
def test_eliminar_las_membresias_y_las_tareas_del_proyecto(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    retired = (
        add_member(
            db,
            "Mi Proyecto",
            "tercer_user",
            ProjectRole.VIEWER,
            left_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )
        if False
        else None
    )
    new_task(client, access_token, project["id"], title="Tarea 1", assigned_to="otro_username")
    new_task(client, access_token, project["id"], title="Tarea 2")
    assert count(db, ProjectMemberModel, project["id"]) == 2
    assert count(db, TaskModel, project["id"]) == 2
    trashed(client, access_token, project)

    permanent(client, access_token, project["id"])

    assert count(db, ProjectMemberModel, project["id"]) == 0
    assert count(db, TaskModel, project["id"]) == 0


# RF-PROJ-10-CA-02
def test_liberar_el_nombre_reservado(client, access_token, project):
    trashed(client, access_token, project)
    reserved = client.post(PROJECTS_URL, json={"name": "mi proyecto"}, headers=bearer(access_token))

    permanent(client, access_token, project["id"])
    free = client.post(PROJECTS_URL, json={"name": "mi proyecto"}, headers=bearer(access_token))

    assert reserved.status_code == 409
    assert free.status_code == 201


# RF-PROJ-10-CA-01
def test_no_listar_ni_poder_restaurar_ni_consultar_el_proyecto_eliminado(
    client, access_token, project
):
    trashed(client, access_token, project)

    permanent(client, access_token, project["id"])
    deleted = client.get(f"{PROJECTS_URL}/deleted", headers=bearer(access_token))
    restored = client.post(f"{PROJECTS_URL}/{project['id']}/restore", headers=bearer(access_token))
    detail = client.get(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token))

    assert deleted.json()["items"] == []
    assert restored.status_code == 404
    assert detail.status_code == 404


# RF-PROJ-10-CA-01
def test_conservar_los_otros_proyectos(client, access_token, other_token, db, project):
    kept = create(client, access_token, name="Se queda")
    foreign = create(client, other_token, name="Mi Proyecto")
    trashed(client, access_token, project)

    permanent(client, access_token, project["id"])

    assert count(db, ProjectModel, kept["id"]) == 1
    assert count(db, ProjectModel, foreign["id"]) == 1


# RF-PROJ-10-DERIVADO
def test_rechazar_un_proyecto_que_no_esta_eliminado(client, access_token, db, project):
    response = permanent(client, access_token, project["id"])

    assert response.status_code == 409
    assert count(db, ProjectModel, project["id"]) == 1
    assert (
        client.get(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token)).status_code
        == 200
    )


# RF-PROJ-10-DERIVADO
def test_rechazar_eliminar_permanentemente_dos_veces(client, access_token, project):
    trashed(client, access_token, project)

    first = permanent(client, access_token, project["id"])
    second = permanent(client, access_token, project["id"])

    assert first.status_code == 204
    assert second.status_code == 404


# RF-PROJ-10-DERIVADO
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_responder_no_encontrado_a_quien_no_es_propietario(
    client, access_token, other_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    trashed(client, access_token, project)

    response = permanent(client, other_token, project["id"])

    assert response.status_code == 404
    assert count(db, ProjectModel, project["id"]) == 1


# RF-PROJ-10-DERIVADO
def test_responder_no_encontrado_a_quien_no_es_miembro(
    client, access_token, other_token, db, project
):
    trashed(client, access_token, project)

    assert permanent(client, other_token, project["id"]).status_code == 404
    assert count(db, ProjectModel, project["id"]) == 1


# RF-PROJ-10-DERIVADO
def test_responder_no_encontrado_si_el_proyecto_no_existe(client, access_token):
    assert permanent(client, access_token, uuid.uuid4()).status_code == 404


# RF-PROJ-10-DERIVADO
def test_rechazar_un_id_que_no_es_uuid(client, access_token):
    assert permanent(client, access_token, "no-es-un-uuid").status_code == 422


# RF-PROJ-10-DERIVADO
def test_rechazar_al_propietario_con_cuenta_desactivada(client, access_token, db, project):
    trashed(client, access_token, project)
    client.post(
        "/api/v1/auth/deactivate",
        json={"current_password": USER["password"]},
        headers=bearer(access_token),
    )

    assert permanent(client, access_token, project["id"]).status_code == 401
    assert count(db, ProjectModel, project["id"]) == 1


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    trashed(client, access_token, project)

    response = client.delete(f"{PROJECTS_URL}/{project['id']}/permanent")

    assert response.status_code == 401
