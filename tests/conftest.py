import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import src.core.models_registry
from src.core.config import settings
from src.core.database import Base, get_db
from src.main import app


@pytest.fixture(scope="session")
def engine():
    url = settings.test_database_url
    if not url or url == settings.database_url or not url.endswith("_test"):
        pytest.exit(
            "La variable TEST_DATABASE_URL no apunta a una base de datos que termine en '_test'",
            returncode=2,
        )
    test_engine = create_engine(url, pool_pre_ping=True)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client(session_factory, engine):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {tables} CASCADE"))


@pytest.fixture
def db(client, session_factory):
    with session_factory() as session:
        yield session
