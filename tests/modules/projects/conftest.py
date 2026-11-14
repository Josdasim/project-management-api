import pytest

# Por revisar en otros modulos de prueba
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
PROJECTS_URL = "/api/v1/projects"
USER = {
    "username": "dana_01",
    "email": "dana@correo.com",
    "password": "passdedana01",
    "first_name": "Dana",
}
OTHER_USER = {**USER, "username": "otro_username", "email": "otro@correo.com"}

# Usados por las pruebas de projects


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()["access_token"]


def create(client, token, **data):
    return client.post(PROJECTS_URL, json=data, headers=bearer(token)).json()


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_token(client, "dana_01")


@pytest.fixture
def other_token(client):
    assert client.post(REGISTER_URL, json=OTHER_USER).status_code == 201
    return login_token(client, "otro_username")
