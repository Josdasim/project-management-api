from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.public import AccountStatus
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from tests.modules.projects.conftest import (
    PROJECTS_URL,
    REGISTER_URL,
    USER,
    access_token,
    bearer,
    create,
    login_token,
    other_token,
    get_project,
    add_member
)


def add(client, token, project_id, **data):
    return client.post(f"{PROJECTS_URL}/{project_id}/members", json=data, headers=bearer(token))


@pytest.fixture
def third_token(client):
    data = {**USER, "username": "tercer_user", "email": "tercer@correo.com"}
    assert client.post(REGISTER_URL, json=data).status_code == 201
    return login_token(client, "tercer_user")


# RF-MEM-01-CA-01
def test_propietario_agrega_un_miembro(client, access_token, other_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = add(client, access_token, project["id"], username="otro_username", role="member")

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "otro_username"
    assert body["role"] == "member"
    assert "joined_at" in body
    detail = get_project(client, other_token, project["id"])
    assert detail.status_code == 200
    assert detail.json()["role"] == "member"


# RF-MEM-01-CA-02
@pytest.mark.parametrize("role", ["admin", "viewer"])
def test_propietario_agrega_administrador_y_observador(client, access_token, other_token, role):
    project = create(client, access_token, name="Mi Proyecto")

    response = add(client, access_token, project["id"], username="otro_username", role=role)

    assert response.status_code == 201
    assert response.json()["role"] == role


# RF-MEM-01-CA-02
@pytest.mark.parametrize("role", ["member", "viewer"])
def test_administrador_agrega_miembro_y_observador(
    client, access_token, other_token, third_token, db, role
):
    project = create(client, access_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = add(client, other_token, project["id"], username="tercer_user", role=role)

    assert response.status_code == 201
    assert response.json()["role"] == role


# RF-MEM-01-CA-02
def test_rechazar_que_el_administrador_asigne_administrador(
    client, access_token, other_token, third_token, db
):
    project = create(client, access_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    response = add(client, other_token, project["id"], username="tercer_user", role="admin")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).status_code == 404


# RF-MEM-01-CA-03
def test_rechazar_asignar_el_rol_propietario(client, access_token, other_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = add(client, access_token, project["id"], username="otro_username", role="owner")

    assert response.status_code == 422


# RF-MEM-01-CA-02
@pytest.mark.parametrize(
    "data",
    [
        {"username": "otro_username", "role": "superman"},
        {"username": "otro_username", "role": None},
        {"username": "otro_username"},
        {"role": "member"},
        {"username": "ot", "role": "member"},
        {"username": "otro_username", "role": "member", "user_id": "x"},
    ],
)
def test_rechazar_datos_invalidos(client, access_token, other_token, data):
    project = create(client, access_token, name="Mi Proyecto")

    assert add(client, access_token, project["id"], **data).status_code == 422


# RF-MEM-01-CA-04
def test_rechazar_cuenta_desactivada(client, access_token, other_token, db):
    project = create(client, access_token, name="Mi Proyecto")
    account = db.scalar(select(AccountModel).where(AccountModel.username == "otro_username"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    response = add(client, access_token, project["id"], username="otro_username", role="member")

    assert response.status_code == 404


# RF-MEM-01-CA-04
def test_rechazar_username_inexistente(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = add(client, access_token, project["id"], username="no_existe", role="member")

    assert response.status_code == 404


# RF-MEM-01-CA-04
def test_rechazar_usuario_que_ya_es_miembro(client, access_token, other_token):
    project = create(client, access_token, name="Mi Proyecto")
    first = add(client, access_token, project["id"], username="otro_username", role="member")
    assert first.status_code == 201

    repeated = add(client, access_token, project["id"], username="otro_username", role="viewer")
    owner = add(client, access_token, project["id"], username="dana_01", role="member")

    assert repeated.status_code == 409
    assert owner.status_code == 409


# RF-MEM-01-CA-05
def test_reincorporar_a_un_antiguo_miembro(client, access_token, other_token, db):
    project = create(client, access_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.VIEWER, left_at=datetime.now(UTC))
    assert get_project(client, other_token, project["id"]).status_code == 404

    response = add(client, access_token, project["id"], username="otro_username", role="member")

    assert response.status_code == 201
    assert response.json()["role"] == "member"
    assert get_project(client, other_token, project["id"]).status_code == 200
    db.expire_all()
    rows = db.scalars(
        select(ProjectMemberModel).where(ProjectMemberModel.role == ProjectRole.MEMBER)
    ).all()
    assert len(rows) == 1
    assert rows[0].left_at is None


# RF-MEM-01-CA-02
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_rechazar_que_miembro_u_observador_agreguen(
    client, access_token, other_token, third_token, db, role
):
    project = create(client, access_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", role)

    response = add(client, other_token, project["id"], username="tercer_user", role="member")

    assert response.status_code == 403
    assert get_project(client, third_token, project["id"]).status_code == 404


# RNF-SEC-03
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = add(client, other_token, project["id"], username="dana_01", role="member")

    assert response.status_code == 404


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = client.post(
        f"{PROJECTS_URL}/{project['id']}/members",
        json={"username": "otro_username", "role": "member"},
    )

    assert response.status_code == 401
