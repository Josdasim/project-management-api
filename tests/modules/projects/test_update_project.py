from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.modules.auth.infrastructure.models import Account as AccountModel
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.infrastructure.models import Project as ProjectModel
from src.modules.projects.infrastructure.models import ProjectMember as ProjectMemberModel

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


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(client, username):
    response = client.post(LOGIN_URL, json={"identifier": username, "password": USER["password"]})

    assert response.status_code == 200
    return response.json()["access_token"]


def create(client, token, **data):
    response = client.post(PROJECTS_URL, json=data, headers=bearer(token))

    assert response.status_code == 201
    return response.json()


def update(client, token, project_id, **data):
    return client.patch(f"{PROJECTS_URL}/{project_id}", json=data, headers=bearer(token))


def add_member(db, project_name, username, role, left_at=None):
    project = db.scalar(select(ProjectModel).where(ProjectModel.name == project_name))
    account = db.scalar(select(AccountModel).where(AccountModel.username == username))
    db.add(
        ProjectMemberModel(
            project_id=project.id,
            user_id=account.user_id,
            role=role,
            joined_at=datetime.now(UTC),
            left_at=left_at,
        )
    )
    db.commit()


@pytest.fixture
def access_token(client):
    assert client.post(REGISTER_URL, json=USER).status_code == 201
    return login_token(client, "dana_01")


@pytest.fixture
def other_token(client):
    assert client.post(REGISTER_URL, json=OTHER_USER).status_code == 201
    return login_token(client, "otro_username")


# RF-PROJ-04-CA-01
def test_propietario_actualiza_nombre_y_descripcion(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = update(client, access_token, project["id"], name="Nuevo Nombre", description="Nueva")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Nuevo Nombre"
    assert body["description"] == "Nueva"
    assert body["role"] == "owner"


# RF-PROJ-04-CA-01 y CA-03
def test_administrador_actualiza_solo_la_descripcion(client, access_token, other_token, db):
    project = create(client, other_token, name="Compartido", description="Original")
    add_member(db, "Compartido", "dana_01", ProjectRole.ADMIN)

    response = update(client, access_token, project["id"], description="Nueva")

    assert response.status_code == 200
    assert response.json()["name"] == "Compartido"
    assert response.json()["description"] == "Nueva"


# RF-PROJ-04-CA-03
@pytest.mark.parametrize(
    "data",
    [
        {"name": "Otro"},
        {"name": "Compartido"},
        {"name": "Otro", "description": "Nueva"},
    ],
)
def test_administrador_no_puede_cambiar_el_nombre(client, access_token, other_token, db, data):
    project = create(client, other_token, name="Compartido", description="Original")
    add_member(db, "Compartido", "dana_01", ProjectRole.ADMIN)

    assert update(client, access_token, project["id"], **data).status_code == 403

    db.expire_all()
    stored = db.scalar(select(ProjectModel))
    assert stored.name == "Compartido"
    assert stored.description == "Original"


# RF-PROJ-04-CA-03
@pytest.mark.parametrize("role", [ProjectRole.MEMBER, ProjectRole.VIEWER])
def test_miembro_y_observador_no_pueden_actualizar(client, access_token, other_token, db, role):
    project = create(client, other_token, name="Compartido")
    add_member(db, "Compartido", "dana_01", role)

    assert update(client, access_token, project["id"], description="x").status_code == 403


# RF-PROJ-04-CA-02
def test_conservar_el_nombre_si_solo_se_envia_la_descripcion(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = update(client, access_token, project["id"], description="Nueva")

    assert response.status_code == 200
    assert response.json()["name"] == "Mi Proyecto"


# RF-PROJ-04-CA-01
@pytest.mark.parametrize(
    "data",
    [
        {"name": ""},
        {"name": "   "},
        {"name": None},
        {"name": "a" * 101},
        {"description": "a" * 5001},
    ],
)
def test_rechazar_datos_invalidos(client, access_token, data):
    project = create(client, access_token, name="Mi Proyecto")

    assert update(client, access_token, project["id"], **data).status_code == 422


# RF-PROJ-04-CA-01
def test_rechazar_nombre_repetido_pero_permitir_el_propio(client, access_token):
    create(client, access_token, name="Alfa")
    project = create(client, access_token, name="Beta")

    assert update(client, access_token, project["id"], name="ALFA").status_code == 409
    assert update(client, access_token, project["id"], name="BETA").status_code == 200


# RF-PROJ-04-CA-04
def test_rechazar_el_campo_owner_id(client, access_token, other_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = update(client, access_token, project["id"], owner_id="cualquier-valor")

    assert response.status_code == 422


# RF-PROJ-04-CA-02
def test_responder_no_encontrado_a_quien_no_es_miembro(client, access_token, other_token):
    project = create(client, other_token, name="Ajeno")

    assert update(client, access_token, project["id"], description="x").status_code == 404


# RF-PROJ-04-CA-02
def test_responder_no_encontrado_si_el_proyecto_esta_eliminado(client, access_token, db):
    project = create(client, access_token, name="Mi Proyecto")
    stored = db.scalar(select(ProjectModel))
    stored.deleted_at = datetime.now(UTC)
    db.commit()

    assert update(client, access_token, project["id"], description="x").status_code == 404


# RF-PROJ-04-DERIVADO
def test_borrar_la_descripcion_con_null(client, access_token):
    project = create(client, access_token, name="Mi Proyecto", description="Original")

    response = update(client, access_token, project["id"], description=None)

    assert response.status_code == 200
    assert response.json()["description"] is None


# RNF-SEC-03
def test_rechazar_peticion_sin_token(client, access_token):
    project = create(client, access_token, name="Mi Proyecto")

    response = client.patch(f"{PROJECTS_URL}/{project['id']}", json={"description": "x"})

    assert response.status_code == 401
