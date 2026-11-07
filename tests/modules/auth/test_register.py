import pytest
from sqlalchemy import func, select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.auth.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.modules.users.infrastructure.models import User as UserModel

URL = "/api/v1/auth/register"
VALID = {
    "username": "Juanito_01",
    "email": "juanito@email.com",
    "password": "pass_de-juanito-123",
    "first_name": "juanito"
}

#RF-AUTH-01_CA-01
def test_registrar_cuenta_datos_validos(client):
    response = client.post(URL, json=VALID)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "juanito_01"
    assert body["email"] == "juanito@email.com"
    assert body["first_name"] == "juanito"

#RF-AUTH-01_CA-02
def test_rechazar_username_repetido(client):
    client.post(URL, json = VALID)
    response = client.post(URL, json = {**VALID, "username":"JUANITO_01", "email":"otro@email.com"})
    assert response.status_code == 409

#RF-AUTH-01_CA-02
def test_rechaza_email_repetido(client):
    client.post(URL, json = VALID)
    response = client.post(URL, json = {**VALID, "username":"JUANITO_02", "email":"juanito@email.com"})

    assert response.status_code == 409

#RF-AUTH-01_CA-03
@pytest.mark.parametrize(
    "override",
    [
        {"usermame": "ab"},
        {"usermame": "a"*31},
        {"usermame": "juan el 1"},
        {"usermame": "juan@correo"},
        {"email":"email-invalido"},
        {"password": "x"*11},
        {"password": "x"*129},
        {"first_name": "  "},
        {"first_name": "a"*101},
        {"last_name": "b"*101},
        {"status": "deactivated"}
    ]
)
def test_rechazar_datos_invalidos(client, override):
    response = client.post(URL, json = {**VALID, **override})

    assert response.status_code == 422

#RF-AUTH-01_CA-04
def test_cuenta_activa(client):
    response = client.post(URL, json = VALID)

    assert response.json()["status"] == "active"

#RF-AUTH-01_CA-05
def test_no_guardar_usuario(client, db, monkeypatch):
    def failling_add(self, accout):
        raise RuntimeError("Fallo simulado...")

    monkeypatch.setattr(SqlAlchemyAccountRepository, "add", failling_add)

    with pytest.raises(RuntimeError):
        client.post(URL, json = VALID)

    assert db.scalar(select(func.count()).select_from(UserModel)) == 0


#RNF-SEC-01_CA-01
def test_guardar_password_como_hash(client, db):
    client.post(URL, json = VALID)
    account = db.scalar(select(AccountModel))

    assert account.password_hash !=VALID["password"]
    assert account.password_hash.startswith("$argon2id$")

#RNF-SEC-01_CA-02
def test_no_exponer_datos_sensibles(client):
    body = client.post(URL, json = VALID).json()

    assert set(body) == {"username", "email", "first_name", "last_name", "status", "created_at"}

#RNF-SEC-01_CA-02
def test_no_repetir_password(client):
    secret = "s3cret-a1c"
    response = client.post(URL, json = {**VALID, "password": secret})

    assert response.status_code == 422
    assert secret not in response.text