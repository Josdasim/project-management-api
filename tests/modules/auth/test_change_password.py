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

PASSWORD_URL = "/api/v1/auth/password"
REFRESH_URL = "/api/v1/auth/refresh"
NEW_PASSWORD = "NuevaClave-2026!"


def login(client, identifier, password):
    return client.post(LOGIN_URL, json={"identifier": identifier, "password": password})


def change_password(client, token, current, new):
    return client.put(
        PASSWORD_URL,
        json={"current_password": current, "new_password": new},
        headers=bearer(token),
    )


def stored_hash(db, username):
    db.expire_all()
    return db.scalar(select(AccountModel).where(AccountModel.username == username)).password_hash


# RF-AUTH-06-CA-01 y CA-02
def test_cambiar_la_contrasena_con_la_actual_correcta(client, access_token):
    response = change_password(client, access_token, USER["password"], NEW_PASSWORD)

    assert response.status_code == 204
    assert response.content == b""


# RF-AUTH-06-CA-01
def test_iniciar_sesion_con_la_nueva_contrasena_y_no_con_la_anterior(client, access_token):
    change_password(client, access_token, USER["password"], NEW_PASSWORD)

    with_new = login(client, USER["username"], NEW_PASSWORD)
    with_old = login(client, USER["username"], USER["password"])

    assert with_new.status_code == 200
    assert with_old.status_code == 401


# RF-AUTH-06-CA-02
def test_rechazar_la_contrasena_actual_incorrecta(client, access_token, db):
    before = stored_hash(db, USER["username"])

    response = change_password(client, access_token, "ClaveIncorrecta-1", NEW_PASSWORD)

    assert response.status_code == 422
    assert stored_hash(db, USER["username"]) == before
    assert login(client, USER["username"], USER["password"]).status_code == 200


# RF-AUTH-06-CA-02
@pytest.mark.parametrize("new_password", ["a" * 11, "a" * 129, ""])
def test_rechazar_una_nueva_contrasena_invalida(client, access_token, db, new_password):
    before = stored_hash(db, USER["username"])

    response = change_password(client, access_token, USER["password"], new_password)

    assert response.status_code == 422
    assert stored_hash(db, USER["username"]) == before


# RF-AUTH-06-CA-02
@pytest.mark.parametrize("new_password", ["a" * 12, "a" * 128])
def test_aceptar_una_nueva_contrasena_en_los_limites(client, access_token, new_password):
    response = change_password(client, access_token, USER["password"], new_password)

    assert response.status_code == 204
    assert login(client, USER["username"], new_password).status_code == 200


# RF-AUTH-06-CA-02
def test_rechazar_una_contrasena_actual_vacia(client, access_token):
    response = change_password(client, access_token, "", NEW_PASSWORD)

    assert response.status_code == 422


# RF-AUTH-06-CA-03
def test_guardar_solo_el_hash_y_distinto_del_anterior(client, access_token, db):
    before = stored_hash(db, USER["username"])

    change_password(client, access_token, USER["password"], NEW_PASSWORD)
    after = stored_hash(db, USER["username"])

    assert after != before
    assert after.startswith("$argon2")
    assert NEW_PASSWORD not in after


# RF-AUTH-06-CA-04
def test_revocar_los_tokens_de_renovacion_anteriores(client, access_token):
    first = login(client, USER["username"], USER["password"]).json()
    second = login(client, USER["username"], USER["password"]).json()

    change_password(client, access_token, USER["password"], NEW_PASSWORD)

    for session in (first, second):
        response = client.post(REFRESH_URL, json={"refresh_token": session["refresh_token"]})
        assert response.status_code == 401


# RF-AUTH-06-CA-04
def test_permitir_nuevas_sesiones_tras_el_cambio(client, access_token):
    change_password(client, access_token, USER["password"], NEW_PASSWORD)

    session = login(client, USER["username"], NEW_PASSWORD).json()
    response = client.post(REFRESH_URL, json={"refresh_token": session["refresh_token"]})

    assert response.status_code == 200


# RF-AUTH-06-DERIVADO
def test_conservar_la_contrasena_de_otros_usuarios(client, access_token, other_token):
    change_password(client, access_token, USER["password"], NEW_PASSWORD)

    response = login(client, OTHER_USER["username"], OTHER_USER["password"])

    assert response.status_code == 200


# RF-AUTH-06-DERIVADO
def test_rechazar_campos_desconocidos(client, access_token):
    response = client.put(
        PASSWORD_URL,
        json={
            "current_password": USER["password"],
            "new_password": NEW_PASSWORD,
            "email": "otro@example.com",
        },
        headers=bearer(access_token),
    )

    assert response.status_code == 422


# RF-AUTH-06-DERIVADO
def test_rechazar_un_cuerpo_incompleto(client, access_token):
    response = client.put(
        PASSWORD_URL, json={"new_password": NEW_PASSWORD}, headers=bearer(access_token)
    )

    assert response.status_code == 422


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client):
    response = client.put(
        PASSWORD_URL, json={"current_password": USER["password"], "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 401
