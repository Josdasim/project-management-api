import pytest
from sqlalchemy import select

from src.core.config import settings
from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.token_provider import JwtTokenProvider

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana01",
    "first_name": "Dana"
}

def bearer(token):
    return {"Authorization": f"Bearer {token}"}

def login_token(client, username):
    response = client.post(
        LOGIN_URL, json = {"identifier": username,"password": USER["password"]}
    )

    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json = USER).status_code == 201
    return login_token(client, "dana_01")

#RF-AUTH-03-CA-01
def test_devolver_datos_cuenta_autenticada(client, access_token):
    response = client.get(ME_URL, headers = bearer(access_token))

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "dana_01"
    assert body["email"] == "dana@correo.com"
    assert body["status"] == "active"

#RF-AUTH-03-CA-02
def test_no_expone_datos_sensibles(client, access_token):
    body = client.get(ME_URL, headers = bearer(access_token)).json()

    assert set(body) == {"username", "email", "status", "created_at"}

#RF-AUTH-03-CA-03
def test_devolver_solo_la_cuenta_del_token(client, access_token):
    other_account = {**USER, "username": "otro_username", "email": "otro@correo.com"}

    assert client.post(REGISTER_URL, json = other_account).status_code == 201
    
    other_account_token = login_token(client, "otro_username")
    assert client.get(ME_URL, headers = bearer(other_account_token)).json()["username"] == "otro_username"
    assert client.get(ME_URL, headers = bearer(access_token)).json()["username"] == "dana_01"

#RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(ME_URL).status_code == 401

#RNF-SEC-02
def test_rechazar_token_invalido(client):
    assert client.get(ME_URL, headers = bearer("novalido")).status_code == 401

#RNF-SEC-02-CA-01
def test_rechazar_token_vencido(client, access_token, db):
    account = db.scalar(select(AccountModel))
    expired = JwtTokenProvider(settings.jwt_secret_key, settings.jwt_algorithm, -1)
    token = expired.create_access_token(account.id)

    assert client.get(ME_URL, headers = bearer(token)).status_code == 401

#RF-AUTH-07-CA-04
def test_cuenta_desactivada_no_permite_acceso(client, access_token, db):
    account = db.scalar(select(AccountModel))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    assert client.get(ME_URL, headers = bearer(access_token)).status_code == 401