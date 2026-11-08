import pytest

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PROFILE_URL = "/api/v1/users/me"
ACCOUNT_URL = "/api/v1/auth/me"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana2026",
    "first_name": "Dana",
    "last_name": "Ruiz",
}


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_token(client, "dana_01")


# RF-USER-02-CA-01
def test_actualizar_nombre_apellido(client, access_token):
    response = client.patch(
        PROFILE_URL,
        json={"first_name": " Daniela ", "last_name": "Perz"},
        headers=bearer(access_token),
    )

    assert response.status_code == 200
    assert response.json() == {"username": "dana_01", "first_name": "Daniela", "last_name": "Perz"}
    assert client.get(PROFILE_URL, headers=bearer(access_token)).json()["first_name"] == "Daniela"


# RF-USER-02-CA-01
@pytest.mark.parametrize(
    "payload",
    [
        {"first_name": ""},
        {"first_name": "   "},
        {"first_name": None},
        {"first_name": "a" * 101},
        {"last_name": ""},
        {"last_name": "b" * 101},
    ],
)
def test_rechazar_datos_invalidos(client, access_token, payload):
    response = client.patch(PROFILE_URL, json=payload, headers=bearer(access_token))
    assert response.status_code == 422


# RF-USER-02-CA-02
@pytest.mark.parametrize(
    "payload",
    [
        {"username": "otro_me"},
        {"email": "otro@correo.com"},
        {"status": "deactivated"},
        {"password": "es_otra-contra?"},
    ],
)
def test_rechazar_otros_campos(client, access_token, payload):
    response = client.patch(PROFILE_URL, json=payload, headers=bearer(access_token))
    assert response.status_code == 422


# RF-USER-02-CA-03
def test_no_modificar_username_ni_email(client, access_token):
    client.patch(PROFILE_URL, json={"first_name": "Daniela"}, headers=bearer(access_token))
    account = client.get(ACCOUNT_URL, headers=bearer(access_token)).json()

    assert account["username"] == "dana_01"
    assert account["email"] == "dana@correo.com"


# RF-USER-02-CA-04
def test_conservar_campos_no_enviados(client, access_token):
    response = client.patch(PROFILE_URL, json={"last_name": "Gómez"}, headers=bearer(access_token))

    assert response.json()["first_name"] == "Dana"
    assert response.json()["last_name"] == "Gómez"


# RF-USER-02-CA-05
def test_borrar_apellido_con_null(client, access_token):
    response = client.patch(PROFILE_URL, json={"last_name": None}, headers=bearer(access_token))

    assert response.status_code == 200
    assert response.json()["last_name"] is None
    assert response.json()["first_name"] == "Dana"


# RF-USER-02-CA-06
def test_solo_modifica_perfil_del_token(client, access_token):
    other = {**USER, "username": "otro_01", "email": "otro@correo.com", "first_name": "Otro"}

    assert client.post(REGISTER_URL, json=other).status_code == 201
    other_token = login_token(client, "otro_01")

    client.patch(PROFILE_URL, json={"first_name": "Cambiado"}, headers=bearer(access_token))

    assert client.get(PROFILE_URL, headers=bearer(other_token)).json()["first_name"] == "Otro"


# RNF-SEC-03
def test_rnf_sec_03_rechaza_peticion_sin_token(client):
    assert client.patch(PROFILE_URL, json={"first_name": "X"}).status_code == 401
