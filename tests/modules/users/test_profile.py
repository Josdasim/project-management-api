import pytest

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PROFILE_URL = "/api/v1/users/me"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana2026",
    "first_name": "Dana",
    "last_name": "Ruiz"
}

def bearer(token):
    return {"Authorization": f"Bearer {token}"}

def login_token(client, username):
    response = client.post(LOGIN_URL, json = {"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json = USER).status_code == 201
    return login_token(client, "dana_01")

#RF-USER-01-CA-01
def test_devolver_perfil_usuario_autenticado(client, access_token):
    response = client.get(PROFILE_URL, headers = bearer(access_token))

    assert response.status_code == 200
    assert response.json() == {"username": "dana_01", "first_name": "Dana", "last_name": "Ruiz"}

#RF-USER-01-CA-02
def test_no_exponer_datos_sensibles(client, access_token):
    body = client.get(PROFILE_URL, headers = bearer(access_token)).json()

    assert set(body) == {"username", "first_name", "last_name"}

#RF-USER-01-CA-03
def test_solo_devolver_perfil_del_token(client, access_token):
    other = {**USER, "username": "otro_01", "email": "otro@correo.com", "first_name": "Otro"}
    assert client.post(REGISTER_URL, json = other).status_code == 201
    other_token = login_token(client, "otro_01")

    assert client.get(PROFILE_URL, headers = bearer(other_token)).json()["first_name"] == "Otro"
    assert client.get(PROFILE_URL, headers = bearer(access_token)).json()["first_name"] == "Dana"

#RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    assert client.get(PROFILE_URL).status_code == 401


