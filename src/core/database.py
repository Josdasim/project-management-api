from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from src.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping = True
)

session_factory = sessionmaker(
    bind = engine,
    autoflush = False,
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = session_factory()

    try:
        yield db
    finally:
        db.close()