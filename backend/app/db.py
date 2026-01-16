import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker


def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://paddock:paddock@localhost:5432/paddock",
    )


def get_engine() -> Engine:
    return create_engine(get_database_url())


SessionLocal = sessionmaker(bind=get_engine())
Base = declarative_base()
