"""Database engine, session factory, and base model.

Uses MySQL via PyMySQL.  The database is created automatically by run.py /
ensure_database() before the engine connects, so the app works without any
manual MySQL setup.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import env

DB_URL = (
    f"mysql+pymysql://{env.mysql_user}:{env.mysql_password}"
    f"@{env.mysql_host}:{env.mysql_port}/{env.mysql_database}?charset=utf8mb4"
)

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,      # detect dropped connections before use
    pool_recycle=280,        # recycle connections before MySQL's wait_timeout
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def ensure_database() -> None:
    """Create the MySQL database if it does not exist.

    Connects to the server without specifying a database and runs
    CREATE DATABASE IF NOT EXISTS.  Safe to call repeatedly.
    """
    from sqlalchemy import text
    from sqlalchemy import create_engine as _ce

    server_url = (
        f"mysql+pymysql://{env.mysql_user}:{env.mysql_password}"
        f"@{env.mysql_host}:{env.mysql_port}/?charset=utf8mb4"
    )
    tmp = _ce(server_url, pool_pre_ping=True)
    try:
        with tmp.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{env.mysql_database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
    finally:
        tmp.dispose()


def init_db() -> None:
    """Create all tables defined on Base.  Safe to call repeatedly."""
    from . import models  # noqa: F401  ensure models are imported

    ensure_database()
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Iterator[Session]:
    """Context manager yielding a DB session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_dep():
    """FastAPI dependency that yields a session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
