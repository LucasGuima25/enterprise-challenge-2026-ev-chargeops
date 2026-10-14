"""Testa persistência em banco de arquivo; PostgreSQL deve ser validado localmente."""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Sessao
from app.seed import preencher


def test_dados_persistem_depois_de_fechar_conexao(tmp_path):
    arquivo = tmp_path / "teste_persistencia.db"
    engine = create_engine(f"sqlite+pysqlite:///{arquivo}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        preencher(db)
        assert len(db.scalars(select(Sessao)).all()) == 3
    engine.dispose()

    outro_engine = create_engine(f"sqlite+pysqlite:///{arquivo}")
    with Session(outro_engine) as db:
        sessoes = db.scalars(select(Sessao)).all()
        assert len(sessoes) == 3
        assert {s.id for s in sessoes} == {"S001", "S002", "S003"}
    outro_engine.dispose()


def test_carga_inicial_idempotente(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'demo.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        preencher(db)
        preencher(db)
        assert len(db.scalars(select(Sessao)).all()) == 3
    engine.dispose()
