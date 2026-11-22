import pytest
from sqlalchemy import select

from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.models import RefreshToken as RefreshTokenModel
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel
from tests.modules.projects.conftest import (
    LOGIN_URL,
    OTHER_USER,
    PROJECTS_URL,
    REGISTER_URL,
    USER,
    access_token,
    add_member,
    bearer,
    create,
    other_token,
)

DEACTIVATE_URL = "/api/v1/auth/deactivate"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/auth/me"


def deactivate(client, token, password):
    return client.post(DEACTIVATE_URL, json={"current_password": password}, headers=bearer(token))


def login(client, identifier, password):
    return client.post(LOGIN_URL, json={"identifier": identifier, "password": password})


def stored_account(db, username):
    db.expire_all()
    return db.scalar(select(AccountModel).where(AccountModel.username == username))


# RF-AUTH-09-CA-01
def test_desactivar_la_cuenta_con_la_contrasena_correcta(client, access_token, db):
    response = deactivate(client, access_token, USER["password"])

    assert response.status_code == 204
    assert response.content == b""
    assert stored_account(db, USER["username"]).status != AccountStatus.ACTIVE


# RF-AUTH-09-CA-01
def test_rechazar_la_contrasena_incorrecta_sin_cambiar_nada(client, access_token, db):
    response = deactivate(client, access_token, "ClaveIncorrecta-1")

    assert response.status_code == 422
    assert stored_account(db, USER["username"]).status == AccountStatus.ACTIVE
    assert client.get(ME_URL, headers=bearer(access_token)).status_code == 200


# RF-AUTH-07-CA-01 y CA-02 / RF-AUTH-09-CA-02
def test_revocar_todos_los_tokens_de_renovacion(client, access_token, db):
    sessions = [login(client, USER["username"], USER["password"]).json() for _ in range(2)]
    account = stored_account(db, USER["username"])

    deactivate(client, access_token, USER["password"])
    db.expire_all()
    tokens = db.scalars(
        select(RefreshTokenModel).where(RefreshTokenModel.account_id == account.id)
    ).all()

    assert len(tokens) >= 2
    assert all(token.revoked_at is not None for token in tokens)
    for session in sessions:
        response = client.post(REFRESH_URL, json={"refresh_token": session["refresh_token"]})
        assert response.status_code == 401


# RF-AUTH-07-CA-03
@pytest.mark.parametrize("identifier", [USER["username"], USER["email"]])
def test_rechazar_el_inicio_de_sesion_de_una_cuenta_desactivada(client, access_token, identifier):
    deactivate(client, access_token, USER["password"])

    assert login(client, identifier, USER["password"]).status_code == 401


# RF-AUTH-07-CA-04
def test_rechazar_el_token_de_acceso_vigente_de_una_cuenta_desactivada(client, access_token):
    deactivate(client, access_token, USER["password"])

    assert client.get(ME_URL, headers=bearer(access_token)).status_code == 401
    assert client.get(PROJECTS_URL, headers=bearer(access_token)).status_code == 401


# RF-AUTH-09
def test_rechazar_desactivar_dos_veces(client, access_token):
    first = deactivate(client, access_token, USER["password"])
    second = deactivate(client, access_token, USER["password"])

    assert first.status_code == 204
    assert second.status_code == 401


# RF-AUTH-09-CA-02 y CA-03
def test_conservar_los_proyectos_y_la_propiedad(client, access_token, other_token, db):
    project = create(client, access_token, name="Mi Proyecto")
    add_member(db, "Mi Proyecto", "otro_username", ProjectRole.ADMIN)

    deactivate(client, access_token, USER["password"])
    db.expire_all()
    stored = db.get(ProjectModel, __import__("uuid").UUID(project["id"]))
    owner_rows = db.scalars(
        select(ProjectMemberModel).where(
            ProjectMemberModel.project_id == stored.id,
            ProjectMemberModel.role == ProjectRole.OWNER,
            ProjectMemberModel.left_at.is_(None),
        )
    ).all()
    seen_by_member = client.get(f"{PROJECTS_URL}/{project['id']}", headers=bearer(other_token))

    assert stored.deleted_at is None
    assert len(owner_rows) == 1
    assert owner_rows[0].user_id == stored.owner_id
    assert seen_by_member.status_code == 200
    assert seen_by_member.json()["role"] == "admin"


# RF-AUTH-09
def test_no_afectar_a_otros_usuarios(client, access_token, other_token):
    deactivate(client, access_token, USER["password"])

    assert client.get(ME_URL, headers=bearer(other_token)).status_code == 200
    assert login(client, OTHER_USER["username"], OTHER_USER["password"]).status_code == 200


# RF-AUTH-09
@pytest.mark.parametrize("field", ["username", "email"])
def test_mantener_reservados_el_username_y_el_correo(client, access_token, field):
    deactivate(client, access_token, USER["password"])
    other_data = {**USER, "username": "nombre_distinto", "email": "distinto@example.com"}
    other_data[field] = USER[field].upper()

    response = client.post(REGISTER_URL, json=other_data)

    assert response.status_code == 409


# RF-AUTH-09
@pytest.mark.parametrize(
    "body",
    [{}, {"current_password": ""}, {"current_password": USER["password"], "extra": 1}],
)
def test_rechazar_un_cuerpo_invalido(client, access_token, db, body):
    response = client.post(DEACTIVATE_URL, json=body, headers=bearer(access_token))

    assert response.status_code == 422
    assert stored_account(db, USER["username"]).status == AccountStatus.ACTIVE


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    response = client.post(DEACTIVATE_URL, json={"current_password": USER["password"]})

    assert response.status_code == 401
