"""Database engine and session helpers."""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common import config

_engine = None
_SessionLocal = None


def _init_engine():
    global _engine, _SessionLocal
    if _engine is None:
        try:
            _engine = create_engine(config.DATABASE_URL)
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            logging.info("Database engine initialized.")
        except Exception as exc:
            logging.critical("Failed to initialize database engine: %s", exc)
            raise


def get_engine():
    """Return the shared SQLAlchemy engine."""
    if _engine is None:
        _init_engine()
    return _engine


def get_session_factory():
    """Return the shared session factory."""
    if _SessionLocal is None:
        _init_engine()
    return _SessionLocal


@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
