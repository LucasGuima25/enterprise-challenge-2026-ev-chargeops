"""Conexão de dados. O banco previsto em produção da Sprint 2 é PostgreSQL."""
from functools import lru_cache
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine():
    # Carregamento tardio evita exigir PostgreSQL nos testes unitários de negócio.
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://chargeops:chargeops_local@localhost:5432/chargeops",
    )
    return create_engine(url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importa modelos para registrar as tabelas no metadata do SQLAlchemy.
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=get_engine())
