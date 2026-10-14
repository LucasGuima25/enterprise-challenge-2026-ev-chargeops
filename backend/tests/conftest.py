"""API integrada sob SQLite em memória; produção mantém PostgreSQL."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models import Carregador, Unidade, Usuario
from decimal import Decimal


@pytest.fixture
def client():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def enable_fks(conn, record):
        conn.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            Unidade(id="A-101", bloco="A", numero="101"),
            Unidade(id="A-102", bloco="A", numero="102"),
            Unidade(id="A-103", bloco="A", numero="103"),
        ])
        db.flush()
        db.add_all([
            Usuario(id="U001", nome="Pessoa fictícia 1", email="u1@exemplo.test", tipo="morador", unidade_id="A-101"),
            Usuario(id="U002", nome="Pessoa fictícia 2", email="u2@exemplo.test", tipo="morador", unidade_id="A-102"),
            Usuario(id="U003", nome="Pessoa fictícia 3", email="u3@exemplo.test", tipo="morador", unidade_id="A-103"),
            Carregador(id="C001", modelo="HCA G2 (simulado)", localizacao="L1 fictício", estado="disponivel", potencia_max_kw=Decimal("22.00")),
        ])
        db.commit()

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as c:
            c.test_engine = engine  # disponibiliza a mesma base isolada a testes de integração IA
            yield c
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
