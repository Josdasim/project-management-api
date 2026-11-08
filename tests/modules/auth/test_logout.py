import pytest
from sqlalchemy import select

from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.models import RefreshToken as RefreshTokenModel

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana01",
    "first_name": "Dana",
}


def login_tokens(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()


def refresh(client, refresh_token):
    return client.post(REFRESH_URL, json={"refresh_token": refresh_token})


def logout(client, refresh_token):
    return client.post(LOGOUT_URL, json={"refresh_token": refresh_token})


@pytest.fixture
def tokens(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_tokens(client, "dana_01")


# RF-AUTH-05-CA-01
def test_cerrar_sesion_revoca_el_token_de_renovacion(client, tokens, db):
    assert logout(client, tokens["refresh_token"]).status_code == 204

    stored = db.scalar(select(RefreshTokenModel))
    assert stored.revoked_at is not None


# RF-AUTH-05-CA-01
def test_no_permite_renovar_con_el_token_de_una_sesion_cerrada(client, tokens):
    assert logout(client, tokens["refresh_token"]).status_code == 204

    assert refresh(client, tokens["refresh_token"]).status_code == 401


# RF-AUTH-05-CA-02
def test_cerrar_sesion_no_desactiva_la_cuenta(client, tokens, db):
    assert logout(client, tokens["refresh_token"]).status_code == 204

    account = db.scalar(select(AccountModel))
    assert account.status == AccountStatus.ACTIVE
    login_tokens(client, "dana_01")


# RF-AUTH-05-CA-01
def test_cerrar_una_sesion_no_afecta_a_las_otras(client, tokens):
    other_session = login_tokens(client, "dana_01")

    assert logout(client, tokens["refresh_token"]).status_code == 204

    assert refresh(client, other_session["refresh_token"]).status_code == 200


# RF-AUTH-05-CA-01
def test_cerrar_sesion_con_token_desconocido_no_da_error(client):
    assert logout(client, "token-que-no-existe").status_code == 204
