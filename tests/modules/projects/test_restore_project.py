import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.domain.enums import AccountStatus
from src.modules.projects.domain.enums import ProjectRole
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)


@pytest.fixture
def project(client, access_token):
    return create(client, access_token, name="Mi Proyecto")


def delete_project(client, token, project_id):
    return client.delete(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


def restore(client, token, project_id):
    return client.post(f"{PROJECTS_URL}/{project_id}/restore", headers=bearer(token))


def get_project(client, token, project_id):
    return client.get(f"{PROJECTS_URL}/{project_id}", headers=bearer(token))


# RF-PROJ-07-CA-01 y CA-03
def test_restaurar_un_proyecto_eliminado(client, access_token, project):
    delete_project(client, access_token, project["id"])

    response = restore(client, access_token, project["id"])

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]
    assert response.json()["name"] == "Mi Proyecto"
    assert response.json()["role"] == "owner"


# RF-PROJ-07-CA-01
def test_consultar_y_listar_el_proyecto_restaurado(client, access_token, project):
    delete_project(client, access_token, project["id"])
    assert get_project(client, access_token, project["id"]).status_code == 404

    restore(client, access_token, project["id"])
    listing = client.get(PROJECTS_URL, headers=bearer(access_token)).json()
    deleted = client.get(f"{PROJECTS_URL}/deleted", headers=bearer(access_token)).json()

    assert get_project(client, access_token, project["id"]).status_code == 200
    assert [item["id"] for item in listing["items"]] == [project["id"]]
    assert deleted["items"] == []


# RF-PROJ-07-CA-03
def test_recuperar_el_acceso_de_los_miembros_activos(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)
    delete_project(client, access_token, project["id"])
    assert get_project(client, other_token, project["id"]).status_code == 404

    restore(client, access_token, project["id"])

    response = get_project(client, other_token, project["id"])
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


# RF-PROJ-07-CA-03
def test_no_recuperar_a_los_miembros_que_ya_se_habian_retirado(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    client.delete(
        f"{PROJECTS_URL}/{project['id']}/members/otro_username", headers=bearer(access_token)
    )
    delete_project(client, access_token, project["id"])

    restore(client, access_token, project["id"])

    assert get_project(client, other_token, project["id"]).status_code == 404


# RF-PROJ-07-CA-03
def test_restaurar_con_un_miembro_de_cuenta_desactivada(
    client, access_token, other_token, db, project
):
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.MEMBER)
    delete_project(client, access_token, project["id"])
    account = db.scalar(select(AccountModel).where(AccountModel.username == "otro_username"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    response = restore(client, access_token, project["id"])

    assert response.status_code == 200
    assert get_project(client, other_token, project["id"]).status_code == 401


# RF-PROJ-07-CA-01
@pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_responder_no_encontrado_a_quien_no_es_propietario(
    client, access_token, other_token, db, project, role
):
    add_member(db, "Mi Proyecto", "otro_username", role)
    delete_project(client, access_token, project["id"])

    response = restore(client, other_token, project["id"])

    assert response.status_code == 404
    assert get_project(client, access_token, project["id"]).status_code == 404


# RF-PROJ-07-CA-01
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token, project):
    delete_project(client, access_token, project["id"])

    assert restore(client, other_token, project["id"]).status_code == 404


# RF-PROJ-07-CA-01
def test_responder_no_encontrado_si_el_proyecto_no_existe(client, access_token):
    import uuid

    assert restore(client, access_token, uuid.uuid4()).status_code == 404


# RF-PROJ-07-CA-04
def test_rechazar_restaurar_un_proyecto_que_no_esta_eliminado(client, access_token, project):
    response = restore(client, access_token, project["id"])

    assert response.status_code == 409
    assert get_project(client, access_token, project["id"]).status_code == 200


# RF-PROJ-07-CA-04
def test_rechazar_restaurar_dos_veces(client, access_token, project):
    delete_project(client, access_token, project["id"])
    first = restore(client, access_token, project["id"])
    second = restore(client, access_token, project["id"])

    assert first.status_code == 200
    assert second.status_code == 409


# RF-PROJ-07-CA-01
def test_rechazar_al_propietario_con_cuenta_desactivada(client, access_token, db, project):
    delete_project(client, access_token, project["id"])
    account = db.scalar(select(AccountModel).where(AccountModel.username == "dana_01"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    assert restore(client, access_token, project["id"]).status_code == 401


# RF-PROJ-07-DERIVADO
def test_rechazar_un_id_que_no_es_uuid(client, access_token):
    assert restore(client, access_token, "no-es-un-uuid").status_code == 422


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token, project):
    delete_project(client, access_token, project["id"])

    response = client.post(f"{PROJECTS_URL}/{project['id']}/restore")

    assert response.status_code == 401
