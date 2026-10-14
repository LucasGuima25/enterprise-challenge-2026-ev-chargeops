"""Dados fictícios fixos; execução idempotente: python -m app.seed"""
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from .database import get_session_factory, init_db
from .models import Unidade, Usuario, Carregador, Sessao


def preencher(db):
    unidades = [Unidade(id=f"A-{i}", bloco="A", numero=str(i)) for i in range(101, 105)]
    for un in unidades:
        if not db.get(Unidade, un.id):
            db.add(un)
    db.flush()
    for i in range(1, 5):
        uid = f"U{i:03d}"
        if not db.get(Usuario, uid):
            db.add(Usuario(id=uid, nome=f"Usuário fictício {i}", email=f"usuario{i}@exemplo.test", tipo="morador", unidade_id=unidades[i-1].id))
    if not db.get(Carregador, "C001"):
        db.add(Carregador(id="C001", modelo="GoodWe HCA G2 (referência simulada)", localizacao="Estacionamento de demonstração", estado="disponivel", potencia_max_kw=Decimal("22.00")))
    db.flush()
    dados = [
        ("S001", "U001", 10, "18.500", "concluida", True),
        ("S002", "U002", 11, "24.000", "concluida", True),
        ("S003", "U004", 12, "10.000", "falha_comunicacao", False),
    ]
    for sid, uid, dia, energia, estado, valido in dados:
        if not db.get(Sessao, sid):
            db.add(Sessao(id=sid, usuario_id=uid, carregador_id="C001",
                          inicio=datetime(2026, 10, dia, 10, tzinfo=timezone.utc),
                          fim=datetime(2026, 10, dia, 13, tzinfo=timezone.utc),
                          energia_kwh=Decimal(energia), estado=estado, origem="simulado", validado=valido))
    db.commit()


def main():
    init_db()
    with get_session_factory()() as db:
        preencher(db)
    print("Exemplo criado. Consulte /api/invoices?period=2026-10. Dados fictícios.")


if __name__ == "__main__":
    main()
