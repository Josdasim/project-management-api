import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from tests.modules.projects.conftest import (
    LOGIN_URL,
    OTHER_USER,
    USER,
    access_token,
    bearer,
    other_token,
)

EMAIL_URL = "/api/v1/auth/email"
ME_URL = "/api/v1/auth/me"
REFRESH_URL = "/api/v1/auth/refresh"
NEW_EMAIL = "nuevo.correo@example.com"


def login(client, identifier, password):
    return client.post(LOGIN_URL, json={"identifier": identifier, "password": password})


def change_email(client, token, password, new_email):
    return client.patch(
        EMAIL_URL,
        json={"new_email": new_email, "current_password": password},
        headers=bearer(token),
    )


def stored_email(db, username):
    db.expire_all()
    return db.scalar(select(AccountModel).where(AccountModel.username == username)).email


# RF-AUTH-08-CA-01 y CA-02
def test_cambiar_el_correo_con_la_contrasena_correcta(client, access_token, db):
    response = change_email(client, access_token, USER["password"], NEW_EMAIL)

    assert response.status_code == 200
    assert response.json()["email"] == NEW_EMAIL
    assert response.json()["username"] == USER["username"]
    assert stored_email(db, USER["username"]) == NEW_EMAIL


# RF-AUTH-08-CA-01
def test_iniciar_sesion_con_el_correo_nuevo(client, access_token):
    change_email(client, access_token, USER["password"], NEW_EMAIL)

    assert login(client, NEW_EMAIL, USER["password"]).status_code == 200
    assert login(client, NEW_EMAIL.upper(), USER["password"]).status_code == 200


# RF-AUTH-08-CA-04
def test_rechazar_el_inicio_de_sesion_con_el_correo_anterior(client, access_token):
    change_email(client, access_token, USER["password"], NEW_EMAIL)

    assert login(client, USER["email"], USER["password"]).status_code == 401
    assert login(client, USER["username"], USER["password"]).status_code == 200


# RF-AUTH-08-CA-03
def test_rechazar_la_contrasena_incorrecta(client, access_token, db):
    response = change_email(client, access_token, "ClaveIncorrecta-1", NEW_EMAIL)

    assert response.status_code == 422
    assert stored_email(db, USER["username"]) == USER["email"]
    assert login(client, USER["email"], USER["password"]).status_code == 200


# RF-AUTH-08-CA-02
@pytest.mark.parametrize(
    "new_email", ["no-es-un-correo", "sin@", "@example.com", "", "a" * 250 + "@example.com"]
)
def test_rechazar_un_correo_invalido(client, access_token, db, new_email):
    response = change_email(client, access_token, USER["password"], new_email)

    assert response.status_code == 422
    assert stored_email(db, USER["username"]) == USER["email"]


# RF-AUTH-08-CA-02
@pytest.mark.parametrize("variant", ["igual", "mayusculas"])
def test_rechazar_un_correo_ya_registrado(client, access_token, other_token, db, variant):
    taken = OTHER_USER["email"] if variant == "igual" else OTHER_USER["email"].upper()

    response = change_email(client, access_token, USER["password"], taken)

    assert response.status_code == 409
    assert stored_email(db, USER["username"]) == USER["email"]
    assert stored_email(db, OTHER_USER["username"]) == OTHER_USER["email"]


# RF-AUTH-08-CA-01
def test_rechazar_peticion_sin_token(client):
    response = client.patch(
        EMAIL_URL, json={"new_email": NEW_EMAIL, "current_password": USER["password"]}
    )

    assert response.status_code == 401


# RF-AUTH-08-DERIVADO
def test_guardar_el_correo_en_minusculas_y_sin_espacios(client, access_token, db):
    response = change_email(client, access_token, USER["password"], "  Nuevo.Correo@Example.COM ")

    assert response.status_code == 200
    assert response.json()["email"] == NEW_EMAIL
    assert stored_email(db, USER["username"]) == NEW_EMAIL


# RF-AUTH-08-DERIVADO
def test_aceptar_el_mismo_correo_sin_cambios(client, access_token, db):
    response = change_email(client, access_token, USER["password"], USER["email"].upper())

    assert response.status_code == 200
    assert response.json()["email"] == USER["email"]
    assert stored_email(db, USER["username"]) == USER["email"]


# RF-AUTH-08-DERIVADO
def test_rechazar_el_mismo_correo_con_contrasena_incorrecta(client, access_token):
    response = change_email(client, access_token, "ClaveIncorrecta-1", USER["email"])

    assert response.status_code == 422


# RF-AUTH-08-DERIVADO
def test_mostrar_el_correo_nuevo_en_auth_me(client, access_token):
    change_email(client, access_token, USER["password"], NEW_EMAIL)

    response = client.get(ME_URL, headers=bearer(access_token))

    assert response.json()["email"] == NEW_EMAIL


# RF-AUTH-08-DERIVADO
def test_conservar_las_sesiones_abiertas(client, access_token):
    session = login(client, USER["username"], USER["password"]).json()

    change_email(client, access_token, USER["password"], NEW_EMAIL)
    response = client.post(REFRESH_URL, json={"refresh_token": session["refresh_token"]})

    assert response.status_code == 200


# RF-AUTH-08-DERIVADO
def test_no_devolver_datos_sensibles(client, access_token):
    body = change_email(client, access_token, USER["password"], NEW_EMAIL).json()

    assert set(body) == {"username", "email", "status", "created_at"}


# RF-AUTH-08-DERIVADO
@pytest.mark.parametrize(
    "body",
    [
        {"current_password": USER["password"]},
        {"new_email": NEW_EMAIL},
        {"new_email": NEW_EMAIL, "current_password": USER["password"], "username": "otro"},
    ],
)
def test_rechazar_un_cuerpo_incompleto_o_con_campos_desconocidos(client, access_token, body):
    response = client.patch(EMAIL_URL, json=body, headers=bearer(access_token))

    assert response.status_code == 422