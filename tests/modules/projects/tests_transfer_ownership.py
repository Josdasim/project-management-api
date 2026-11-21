import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.public import AccountStatus
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
    third_token,
)


def transfer(client, token, project_id, username):
    return client.post(
        f"{PROJECTS_URL}/{project_id}/transfer-ownership",
        json={"username": username},
        headers=bearer(token),
    )


def role_of(client, token, project_id):
    return client.get(f"{PROJECTS_URL}/{project_id}", headers=bearer(token)).json()["role"]


def owners(db, project_id):
    db.expire_all()
    return db.scalars(
        select(ProjectMemberModel).where(
            ProjectMemberModel.project_id == uuid.UUID(project_id),
            ProjectMemberModel.role == ProjectRole.OWNER,
            ProjectMemberModel.left_at.is_(None),
        )
    ).all()


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")


# RF-PROJ-08-CA-01 y CA-02
def test_transferir_la_propiedad_a_un_administrador(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 200
    assert response.json()["username"] == "otro_username"
    assert response.json()["role"] == "owner"
    assert role_of(client, other_token, project["id"]) == "owner"
    assert role_of(client, access_token, project["id"]) == "admin"


# RF-PROJ-08-CA-02
def test_dejar_un_solo_propietario_y_actualizar_el_owner_id(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    transfer(client, access_token, project["id"], "otro_username")
    current = owners(db, project["id"])
    stored = db.get(ProjectModel, uuid.UUID(project["id"]))

    assert len(current) == 1
    assert stored.owner_id == current[0].user_id


# RF-PROJ-08-CA-01
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_transferir_a_un_miembro_u_observador(client, access_token, other_token, db, project, role):
    add_member(db, "Mi Proyecto", "otro_username", role)

    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 200
    assert role_of(client, other_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
def test_transferir_sin_distinguir_mayusculas(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)

    response = transfer(client, access_token, project["id"], "OTRO_USERNAME")

    assert response.status_code == 200
    assert response.json()["username"] == "otro_username"


# RF-PROJ-08-CA-01
def test_rechazar_un_destino_que_no_es_miembro(client, access_token, third_token, project):
    response = transfer(client, access_token, project["id"], "tercer_user")

    assert response.status_code == 422
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
def test_rechazar_un_username_inexistente(client, access_token, project):
    response = transfer(client, access_token, project["id"], "no_existe")

    assert response.status_code == 422


# RF-PROJ-08-CA-01
def test_rechazar_transferirse_a_si_mismo(client, access_token, project):
    response = transfer(client, access_token, project["id"], "dana_01")

    assert response.status_code == 422
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
def test_rechazar_un_destino_con_cuenta_desactivada(client, access_token, other_token, db, project):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    account = db.scalar(select(AccountModel).where(AccountModel.username == "otro_username"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()
    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 422
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
def test_rechazar_un_destino_con_membresia_finalizada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN, left_at=datetime.now(UTC))

    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 422
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-CA-03
def test_rechazar_si_el_destino_ya_tiene_un_proyecto_con_ese_nombre(
    client, access_token, other_token, db, project
):
    create(client, other_token, name="mi proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 409
    assert role_of(client, access_token, project["id"]) == "owner"
    assert role_of(client, other_token, project["id"]) == "admin"


# RF-PROJ-08-CA-03
def test_rechazar_si_el_proyecto_del_destino_con_ese_nombre_esta_eliminado(
    client, access_token, other_token, db, project
):
    hidden = create(client, other_token, name="Mi Proyecto")
    client.delete(f"{PROJECTS_URL}/{hidden['id']}", headers=bearer(other_token))
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = transfer(client, access_token, project["id"], "otro_username")

    assert response.status_code == 409


# RF-PROJ-08-CA-03
def test_transferir_despues_de_cambiar_el_nombre(client, access_token, other_token, db, project):
    create(client, other_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    renamed = client.patch(
        f"{PROJECTS_URL}/{project['id']}",
        json={"name": "Nombre Nuevo"},
        headers=bearer(access_token),
    )

    response = transfer(client, access_token, project["id"], "otro_username")

    assert renamed.status_code == 200
    assert response.status_code == 200


# RF-PROJ-08-CA-05
def test_rechazar_una_segunda_transferencia_del_propietario_anterior(
    client, access_token, other_token, third_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    first = transfer(client, access_token, project["id"], "otro_username")
    second = transfer(client, access_token, project["id"], "tercer_user")

    assert first.status_code == 200
    assert second.status_code == 403
    assert len(owners(db, project["id"])) == 1
    assert role_of(client, other_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_rechazar_a_quien_no_es_propietario(
    client, access_token, other_token, third_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    add_member(db, "Mi Proyecto", "tercer_user", ProjectRole.MEMBER)

    response = transfer(client, other_token, project["id"], "tercer_user")

    assert response.status_code == 403
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-DERIVADO
def test_el_propietario_anterior_ya_no_puede_eliminar_el_proyecto(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    transfer(client, access_token, project["id"], "otro_username")

    response = client.delete(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token))

    assert response.status_code == 403


# RF-PROJ-08-DERIVADO
def test_el_nuevo_propietario_puede_eliminar_el_proyecto(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    transfer(client, access_token, project["id"], "otro_username")

    response = client.delete(f"{PROJECTS_URL}/{project['id']}", headers=bearer(other_token))

    assert response.status_code == 204


# MEM-05.5
def test_abandonar_como_administrador_despues_de_transferir(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    transfer(client, access_token, project["id"], "otro_username")

    response = client.delete(
        f"{PROJECTS_URL}/{project['id']}/members/me", headers=bearer(access_token)
    )

    assert response.status_code == 204


# RF-PROJ-08-DERIVADO
@pytest.mark.parametrize(
    "body",
    [{}, {"username": "ab"}, {"username": "otro_username", "role": "owner"}],
)
def test_rechazar_un_cuerpo_invalido(client, access_token, other_token, db, project, body):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = client.post(
        f"{PROJECTS_URL}/{project['id']}/transfer-ownership",
        json=body,
        headers=bearer(access_token),
    )

    assert response.status_code == 422
    assert role_of(client, access_token, project["id"]) == "owner"


# RF-PROJ-08-CA-01
def test_responder_no_encontrado_a_quien_no_es_miembro(client, other_token, project):
    assert transfer(client, other_token, project["id"], "dana_01").status_code == 404


# RF-PROJ-08-CA-01
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    client.delete(f"{PROJECTS_URL}/{project['id']}", headers=bearer(access_token))

    assert transfer(client, access_token, project["id"], "otro_username").status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, project):
    response = client.post(
        f"{PROJECTS_URL}/{project['id']}/transfer-ownership", json={"username": "otro_username"}
    )

    assert response.status_code == 401
