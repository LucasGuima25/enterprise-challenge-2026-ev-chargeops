"""Testes de IA de ponta a ponta pela API real usando banco isolado."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence import atributos_dia, anomalias_sessoes, previsao_demanda
from app.models import Sessao
from app.seed_history import adicionar_historico


def carregar(client):
    with Session(client.test_engine) as db:
        return adicionar_historico(db)


def test_ia_sem_historico_retorna_insuficiente_sem_quebrar(client):
    p = client.get('/api/ai/forecast')
    a = client.get('/api/ai/anomalies')
    r = client.get('/api/ai/recommendations')
    assert p.status_code == a.status_code == r.status_code == 200
    assert p.json()['status'] == 'dados_insuficientes'
    assert a.json()['status'] == 'dados_insuficientes'
    assert r.json()['status'] == 'parcial'
    assert len(r.json()['recomendacoes']) == 2


def test_carga_historica_idempotente_e_exclusivamente_sintetica(client):
    quantidade = carregar(client)
    assert quantidade >= 70
    assert carregar(client) == 0
    dados = client.get('/api/sessions').json()
    assert len(dados) == quantidade
    assert all(s['origem'] == 'simulado' for s in dados)
    assert len(set(s['id'] for s in dados)) == quantidade


def test_endpoint_ia_treina_e_retorna_metricas_honestas(client):
    carregar(client)
    primeiro = client.get('/api/ai/forecast')
    segundo = client.get('/api/ai/forecast')
    assert primeiro.status_code == 200, primeiro.text
    dados = primeiro.json()
    assert dados == segundo.json()  # determinismo com sementes fixas
    assert dados['status'] == 'ok'
    assert dados['metricas']['treino_dias'] >= 20
    assert dados['metricas']['teste_dias'] >= 7
    assert dados['metricas']['mae_modelo_kwh'] >= 0
    assert dados['metricas']['mae_baseline_media_7d_kwh'] >= 0
    assert isinstance(dados['metricas']['supera_baseline'], bool)
    assert len(dados['previsoes']) == 7
    assert all(p['kwh_previstos'] >= 0 for p in dados['previsoes'])
    assert dados['fonte'] == 'sessoes_validadas_do_banco'


def test_anomalias_e_recomendacoes_geradas_dos_modelos(client):
    carregar(client)
    anomalias = client.get('/api/ai/anomalies').json()
    recomendacoes = client.get('/api/ai/recommendations').json()
    assert anomalias['status'] == 'ok'
    assert anomalias['total_anomalias'] > 0
    assert any(x['sessao_id'] == 'H20260915A' for x in anomalias['anomalias'])
    assert all(a['score'] < 0 for a in anomalias['anomalias'])
    assert any(x['tipo'] == 'revisao' and 'H20260915A' in x['evidencia'] for x in recomendacoes['recomendacoes'])
    assert recomendacoes['status'] == 'ok'


def test_sessao_nova_altera_faturamento_e_analises_mesma_base(client):
    carregar(client)
    antes_p = client.get('/api/ai/forecast').json()
    antes_a = client.get('/api/ai/anomalies').json()
    antes_f = client.get('/api/invoices?period=2026-10').json()
    payload = {"id": "NOVA100", "usuario_id": "U001", "carregador_id": "C001",
               "inicio": "2026-10-20T09:00:00-03:00", "fim": "2026-10-20T11:00:00-03:00",
               "energia_kwh": "10.0", "estado": "concluida", "origem": "simulado", "validado": True}
    r = client.post('/api/sessions', json=payload)
    assert r.status_code == 201, r.text
    depois_p = client.get('/api/ai/forecast').json()
    depois_a = client.get('/api/ai/anomalies').json()
    depois_f = client.get('/api/invoices?period=2026-10').json()
    assert antes_p['periodo_historico']['fim'] != depois_p['periodo_historico']['fim']
    assert depois_a['sessoes_analisadas'] == antes_a['sessoes_analisadas'] + 1
    assert Decimal(depois_f[0]['total']) - Decimal(antes_f[0]['total']) == Decimal('14.00')
    assert depois_p['sessoes_analisadas'] == antes_p['sessoes_analisadas'] + 1


def test_pendencia_excluida_de_treinamento_e_fatura(client):
    carregar(client)
    antes = client.get('/api/ai/forecast').json()
    anomal = client.get('/api/ai/anomalies').json()
    payload = {"id": "PENDENTE101", "usuario_id": "U001", "carregador_id": "C001",
               "inicio": "2026-10-29T09:00:00-03:00", "fim": "2026-10-29T12:00:00-03:00",
               "energia_kwh": "50", "estado": "falha_comunicacao", "origem": "simulado", "validado": False}
    assert client.post('/api/sessions', json=payload).status_code == 201
    assert client.get('/api/ai/forecast').json() == antes
    assert client.get('/api/ai/anomalies').json() == anomal
    f = client.get('/api/invoices?period=2026-10').json()[0]
    assert f['sessoes_pendentes'] == 1 and Decimal(f['total']) == 0


def test_atributos_do_dia_nao_dependem_do_proprio_consumo():
    datas = [date(2026, 7, 1) + timedelta(days=i) for i in range(9)]
    y1 = [1., 2., 3., 4., 5., 6., 7., 100., 3.]
    y2 = [1., 2., 3., 4., 5., 6., 7., 999., 3.]
    assert atributos_dia(datas[7], 7, y1) == atributos_dia(datas[7], 7, y2)
