import pytest
from sqlalchemy import select

from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.infrastructure.models import Account as AccountModel

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
SEARCH_URL = "/api/v1/users/search"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana2026",
    "first_name": "Dana",
}
TARGET = {
    "username": "maria_01",
    "email": "maria@correo.com",
    "password": "passdemaria2026",
    "first_name": "Maria",
    "last_name": "Gomez",
}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    assert client.post(REGISTER_URL, json=TARGET).status_code == 201
    response = client.post(LOGIN_URL, json={"identifier": "dana_01", "password": USER["password"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def search(client, token, **params):
    return client.get(SEARCH_URL, params=params, headers=bearer(token))


# RF-USER-04-CA-01
def test_rechazar_busqueda_sin_criterio(client, access_token):
    assert search(client, access_token).status_code == 422


# RF-USER-04-CA-01
def test_rechazar_busqueda_con_dos_criterios(client, access_token):
    response = search(client, access_token, username="maria_01", email="maria@correo.com")

    assert response.status_code == 422


# RF-USER-04-CA-02
@pytest.mark.parametrize(
    "criterio",
    [
        {"username": "maria_01"},
        {"username": "MARIA_01"},
        {"email": "maria@correo.com"},
        {"email": "MARIA@CORREO.COM"},
    ],
)
def test_coincidencia_exacta_sin_distinguir_mayusculas(client, access_token, criterio):
    response = search(client, access_token, **criterio)

    assert response.status_code == 200
    assert response.json()["username"] == "maria_01"


# RF-USER-04-CA-02
@pytest.mark.parametrize("criterio", [{"username": "mari"}, {"email": "maria@"}])
def test_una_coincidencia_parcial_no_encuentra(client, access_token, criterio):
    assert search(client, access_token, **criterio).status_code == 404


# RF-USER-04-CA-03
def test_ignorar_cuentas_desactivadas(client, access_token, db):
    account = db.scalar(select(AccountModel).where(AccountModel.username == "maria_01"))
    account.status = AccountStatus.DEACTIVATED
    db.commit()

    assert search(client, access_token, username="maria_01").status_code == 404


# RF-USER-04-CA-04
def test_responder_404_si_no_hay_coincidencia(client, access_token):
    response = search(client, access_token, username="nadie_007")

    assert response.status_code == 404
    assert response.json() == {"detail": "Usuario no encontrado"}


# RF-USER-04-CA-05
def test_devuelve_solo_datos_publicos(client, access_token):
    body = search(client, access_token, username="maria_01").json()

    assert body == {"username": "maria_01", "first_name": "Maria", "last_name": "Gomez"}


# RN-SEC-CA-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(SEARCH_URL, params={"username": "maria_01"}).status_code == 401
