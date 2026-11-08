from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.models import RefreshToken as RefreshTokenModel

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
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


@pytest.fixture
def tokens(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_tokens(client, "dana_01")


# RF-AUTH-04-CA-01
def test_renovar_con_token_valido(client, tokens):
    response = refresh(client, tokens["refresh_token"])

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "refresh_token", "token_type"}
    assert body["refresh_token"] != tokens["refresh_token"]


# RF-AUTH-04-CA-02
def test_revocar_token_anterior_al_renovar(client, tokens):
    assert refresh(client, tokens["refresh_token"]).status_code == 200

    assert refresh(client, tokens["refresh_token"]).status_code == 401


# RF-AUTH-04-CA-03
def test_rechazar_token_de_renovacion_invalido(client, tokens):
    assert refresh(client, tokens["refresh_token"] + "x").status_code == 401


# RF-AUTH-04-CA-03
def test_rechazar_token_de_renovacion_vencido(client, tokens, db):
    stored = db.scalar(select(RefreshTokenModel))
    stored.expires_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()

    assert refresh(client, tokens["refresh_token"]).status_code == 401


# RF-AUTH-04-CA-04
def test_rechazar_renovacion_con_cuenta_desactivada(client, tokens, db):
    account = db.scalar(select(AccountModel))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    assert refresh(client, tokens["refresh_token"]).status_code == 401


# RNF-SEC-02-CA-04
def test_reutilizar_token_revocado_invalida_todas_las_sesiones(client, tokens, db):
    renewed = refresh(client, tokens["refresh_token"]).json()

    assert refresh(client, tokens["refresh_token"]).status_code == 401
    assert refresh(client, renewed["refresh_token"]).status_code == 401

    db.expire_all()
    stored = db.scalars(select(RefreshTokenModel)).all()
    assert all(token.revoked_at is not None for token in stored)
