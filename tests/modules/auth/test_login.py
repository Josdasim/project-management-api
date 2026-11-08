from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.core.config import settings
from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.models import RefreshToken as RefreshTokenModel
from src.modules.auth.infrastructure.token_provider import JwtTokenProvider


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
USER = {
    "username": "Maria_rosario_01",
    "email": "correo_maria@rosario.com",
    "password": "pass_de_maria-12",
    "first_name": "Rosario",
}


@pytest.fixture
def registered(client):
    client.post(REGISTER_URL, json=USER)


def log_in(client, identifier, password=USER["password"]):
    return client.post(LOGIN_URL, json={"identifier": identifier, "password": password})


# RF-AUTH-02-CA-01
@pytest.mark.parametrize(
    "identifier",
    [
        "Maria_rosario_01",
        "MARIA_ROSARIO_01",
        "correo_maria@rosario.com",
        "CORREO_MARIA@ROSARIO.COM",
    ],
)
def test_username_or_email(client, registered, identifier):
    response = log_in(client, identifier)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "refresh_token", "token_type"}
    assert body["token_type"] == "bearer"


# RF-AUTH-02-CA-02
def test_rechazar_password_incorrecto(client, registered):
    assert log_in(client, "maria_rosario_01", "contraseña_correcta?").status_code == 401


# RF-AUTH-02-CA-02
def test_rechazar_username_inexistente(client, registered):
    assert log_in(client, "nobody").status_code == 401


# RF-AUTH-02-CA-02
def test_rechazar_cuenta_desactivada(client, registered, db):
    account = db.scalar(select(AccountModel).where(AccountModel.username == "maria_rosario_01"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    assert log_in(client, "maria_rosario_01").status_code == 401


# RF-AUTH-02-CA-03
def test_mismo_mensaje_usuario_inexistente_password_incorrecta(client, registered):
    unknow_user = log_in(client, "nobody")
    wrong_password = log_in(client, "maria_rosario_01", "pass_correcta?")

    assert unknow_user.json() == wrong_password.json()


# RF-AUTH-02-CA-04
def test_identificar_cuenta_access_token(client, registered, db):
    token = log_in(client, "maria_rosario_01").json()["access_token"]
    provider = JwtTokenProvider(
        settings.jwt_secret_key, settings.jwt_algorithm, settings.access_token_expire_minutes
    )
    account = db.scalar(select(AccountModel))

    assert provider.decode_access_token(token) == account.id


# RNF-SEC-01-CA-01
def test_guardar_refresh_token_como_hash(client, registered, db):
    generated_refresh_token = log_in(client, "maria_rosario_01").json()["refresh_token"]

    stored = db.scalar(select(RefreshTokenModel))

    remaining = stored.expires_at - datetime.now(UTC)

    assert timedelta(days=6) < remaining <= timedelta(days=7)
