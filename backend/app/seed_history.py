"""Cria histórico sintético fixo para avaliação da IA. Idempotente.

Uso: python -m app.seed_history (precisa DATABASE_URL apontar ao PostgreSQL).
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from random import Random
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session_factory, init_db
from .models import Carregador, Sessao, Usuario
from .seed import preencher

SP = ZoneInfo("America/Sao_Paulo")


def adicionar_historico(db: Session) -> int:
    """Não altera registros da Etapa 1; escreve apenas sessões H*."""
    usuarios = db.scalars(select(Usuario).order_by(Usuario.id)).all()
    carregador = db.get(Carregador, "C001")
    if not usuarios or not carregador:
        raise ValueError("Cadastre usuários e o carregador C001 antes de gerar histórico.")
    rng = Random(20261013)
    novo = 0
    inicio = date(2026, 7, 1)
    fim = date(2026, 9, 30)
    dia = inicio
    indice = 0
    while dia <= fim:
        # Padrão sazonal de ocupação com dias ociosos e poucos usos no fim de semana.
        probabilidade = 0.87 if dia.weekday() < 5 else 0.60
        if rng.random() < probabilidade:
            quantidade = 2 if rng.random() < (0.65 if dia.weekday() < 5 else 0.35) else 1
            for hora_num in range(quantidade):
                sid = f"H{dia:%Y%m%d}{'A' if hora_num == 0 else 'B'}"
                hora = 9 if hora_num == 0 else 16
                duracao = round(rng.uniform(1.0, 2.8), 2)
                potencia = rng.uniform(4.5, 10.5)
                energia = duracao * potencia
                if dia == date(2026, 9, 15) and hora_num == 0:
                    duracao, energia = 3.0, 47.0  # sessão válida, mas rara: 15,67 kW
                estado = "interrompida" if indice % 39 == 0 else "concluida"
                indice += 1
                if not db.get(Sessao, sid):
                    local = datetime(dia.year, dia.month, dia.day, hora, tzinfo=SP)
                    comeco = local.astimezone(timezone.utc)
                    db.add(Sessao(
                        id=sid, usuario_id=usuarios[indice % len(usuarios)].id,
                        carregador_id="C001", inicio=comeco,
                        fim=comeco + timedelta(hours=duracao),
                        energia_kwh=Decimal(str(round(energia, 3))),
                        estado=estado, origem="simulado", validado=True,
                    ))
                    novo += 1
        dia += timedelta(days=1)
    db.commit()
    return novo


def main():
    init_db()
    with get_session_factory()() as db:
        preencher(db)
        adicionadas = adicionar_historico(db)
    print(f"Histórico fictício sincronizado: {adicionadas} sessões novas, julho–setembro/2026.")
    print("Consulte /api/ai/forecast, /api/ai/anomalies e /api/ai/recommendations.")


if __name__ == "__main__":
    main()
