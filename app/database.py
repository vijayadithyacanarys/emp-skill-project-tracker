import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

database_url = make_url(DATABASE_URL)
database_backend = database_url.get_backend_name()
if database_backend not in {"mssql", "postgresql"}:
    raise RuntimeError(
        "DATABASE_URL must use the MSSQL or PostgreSQL dialect"
    )
if (
    database_backend == "mssql"
    and database_url.drivername != "mssql+pyodbc"
):
    raise RuntimeError(
        "MSSQL DATABASE_URL must use the mssql+pyodbc driver"
    )

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()