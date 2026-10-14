"""Executa demonstração real por HTTP local (FastAPI TestClient + SQLite temporário).

Não depende de Docker nem gera prints falsos; resultados saem dos endpoints.
Uso: python -m app.demo_ia [--saida caminho.json]
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from .database import Base, get_db
from .main import app
from .seed import preencher
from .seed_history import adicionar_historico


def demonstrar() -> dict:
    engine = create_engine('sqlite+pysqlite:///:memory:',
                           connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as sessao:
        preencher(sessao)
        inseridos = adicionar_historico(sessao)

    def banco_teste():
        with Session(engine) as sessao:
            yield sessao

    app.dependency_overrides[get_db] = banco_teste
    try:
        with TestClient(app) as client:
            urls = {
                'saude': '/api/health', 'faturas_outubro': '/api/invoices?period=2026-10',
                'previsao': '/api/ai/forecast', 'anomalias': '/api/ai/anomalies',
                'recomendacoes': '/api/ai/recommendations',
            }
            dados = {}
            for nome, url in urls.items():
                resposta = client.get(url)
                resposta.raise_for_status()
                dados[nome] = resposta.json()
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert dados['previsao']['status'] == 'ok'
    assert dados['anomalias']['status'] == 'ok'
    assert dados['recomendacoes']['status'] == 'ok'
    assert dados['anomalias']['total_anomalias'] > 0
    faturas = {f['usuario_id']: f for f in dados['faturas_outubro']}
    assert Decimal(faturas['U001']['total']) == Decimal('21.65')
    assert Decimal(faturas['U002']['total']) == Decimal('26.60')

    return {
        'contexto': 'EV ChargeOps - demonstracao funcional, simulacao didatica; sem equipamento GoodWe real',
        'ambiente': 'FastAPI TestClient + banco SQLite isolado (PostgreSQL permanece configuracao padrao da aplicacao)',
        'sessoes_historicas_novas': inseridos,
        'respostas_api': dados,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--saida', help='Grava JSON com as respostas reais da API no caminho informado')
    argumentos = parser.parse_args()
    resposta = demonstrar()
    print(f"Historico sintetico: {resposta['sessoes_historicas_novas']} sessoes geradas.")
    metricas = resposta['respostas_api']['previsao']['metricas']
    print('Previsao: 7 dias | MAE modelo:', metricas['mae_modelo_kwh'],
          '| MAE media movel:', metricas['mae_baseline_media_7d_kwh'],
          '| supera baseline:', metricas['supera_baseline'])
    print('Anomalias identificadas:', resposta['respostas_api']['anomalias']['total_anomalias'])
    print('Recomendacoes:', len(resposta['respostas_api']['recomendacoes']['recomendacoes']))
    print('Faturas outubro: U001 R$ 21,65; U002 R$ 26,60.')
    if argumentos.saida:
        destino = Path(argumentos.saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(resposta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('Respostas de API gravadas em:', destino.resolve())


if __name__ == '__main__':
    main()
