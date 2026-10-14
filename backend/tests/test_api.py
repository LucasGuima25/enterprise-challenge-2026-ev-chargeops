from decimal import Decimal as D


def dados(sid="S001", usuario="U001", start="2026-10-10T10:00:00-03:00", end="2026-10-10T12:00:00-03:00", kwh="18.500", estado="concluida", valido=True):
    return {"id":sid,"usuario_id":usuario,"carregador_id":"C001","inicio":start,"fim":end,"energia_kwh":kwh,"estado":estado,"origem":"simulado","validado":valido}


def test_saude_e_catalogos(client):
    assert client.get("/api/health").status_code == 200
    assert len(client.get("/api/users").json()) == 3
    assert len(client.get("/api/chargers").json()) == 1


def test_cadastro_rateio_e_periodo(client):
    r=client.post("/api/sessions",json=dados())
    assert r.status_code == 201, r.text
    assert r.json()["inicio"].endswith("Z") or r.json()["inicio"].endswith("+00:00")
    sess=client.get("/api/sessions?period=2026-10")
    assert len(sess.json())==1
    f={x["usuario_id"]: x for x in client.get("/api/invoices?period=2026-10").json()}
    assert D(f["U001"]["total"]) == D("21.65")
    assert D(f["U003"]["total"]) == D("0.00")


def test_varias_sessoes_mes_sem_duplicar_taxa(client):
    assert client.post("/api/sessions",json=dados(kwh="10")).status_code == 201
    assert client.post("/api/sessions",json=dados("S002", "U001", "2026-10-11T10:00:00-03:00", "2026-10-11T12:00:00-03:00", "15")).status_code == 201
    u1=client.get("/api/invoices?period=2026-10").json()[0]
    assert D(u1["total"]) == D("27.50") and u1["sessoes_cobradas"] == 2


def test_falha_pendente_nao_faturada(client):
    r=client.post("/api/sessions",json=dados(kwh="33",estado="falha_comunicacao",valido=False))
    assert r.status_code == 201, r.text
    f=client.get("/api/invoices?period=2026-10").json()[0]
    assert f["sessoes_pendentes"] == 1 and D(f["total"]) == 0


def test_interrompida_validada_e_cobrada(client):
    r=client.post("/api/sessions",json=dados(estado="interrompida",kwh="4"))
    assert r.status_code == 201, r.text
    assert D(client.get("/api/invoices?period=2026-10").json()[0]["total"]) == D("8.60")


def test_rejeicao_id_e_sobreposicao(client):
    assert client.post("/api/sessions",json=dados()).status_code == 201
    assert client.post("/api/sessions",json=dados()).status_code == 409
    assert client.post("/api/sessions",json=dados("S002", "U002", "2026-10-10T11:00:00-03:00", "2026-10-10T13:00:00-03:00")).status_code == 409
    assert len(client.get("/api/sessions").json()) == 1


def test_rejeicao_dados_invalidos(client):
    assert client.post("/api/sessions",json=dados(kwh="-1")).status_code == 422
    assert client.post("/api/sessions",json=dados(end="2026-10-10T09:00:00-03:00")).status_code == 422
    assert client.post("/api/sessions",json=dados(start="2026-10-10T10:00:00",end="2026-10-10T11:00:00")).status_code == 422
    assert client.post("/api/sessions",json=dados(estado="falha_comunicacao",valido=True)).status_code == 422
    assert client.post("/api/sessions",json=dados(usuario="U999")).status_code == 404
    assert len(client.get("/api/sessions").json()) == 0


def test_atribuicao_mes_local_entre_utc_e_sao_paulo(client):
    # 1 de novembro em UTC, ainda 31/outubro em São Paulo.
    r=client.post("/api/sessions",json=dados(start="2026-11-01T01:00:00+00:00",end="2026-11-01T02:00:00+00:00"))
    assert r.status_code == 201, r.text
    assert len(client.get("/api/sessions?period=2026-10").json()) == 1
    assert len(client.get("/api/sessions?period=2026-11").json()) == 0


def test_periodo_invalido(client):
    assert client.get("/api/invoices?period=2026-13").status_code == 422


def test_frontend_cors_preflight(client):
    origem = "http://127.0.0.1:5173"
    resposta = client.options("/api/sessions", headers={
        "Origin": origem, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert resposta.status_code == 200
    assert resposta.headers.get("access-control-allow-origin") == origem


def test_fluxo_formulario_rateio_e_ia(client):
    """Mesmo cadastro pela API pode ser consultado por sessões, faturas e IA."""
    previa = client.get("/api/invoices?period=2026-10").json()
    assert sum(float(x["energia_kwh"]) for x in previa) == 0
    cadastro = client.post("/api/sessions", json=dados(sid="FORM01", kwh="10.000"))
    assert cadastro.status_code == 201
    assert cadastro.json()["id"] == "FORM01"
    assert any(s["id"] == "FORM01" for s in client.get("/api/sessions").json())
    faturas = client.get("/api/invoices?period=2026-10").json()
    assert D(next(x for x in faturas if x["usuario_id"] == "U001")["total"]) == D("14.00")
    ia = client.get("/api/ai/anomalies").json()
    assert ia["sessoes_analisadas"] == 1
    assert ia["status"] == "dados_insuficientes"


def test_config_exibe_tarifas_reais(client, monkeypatch):
    monkeypatch.setenv("TARIFA_KWH", "1.27")
    monkeypatch.setenv("MANUTENCAO_MENSAL", "8.50")
    resposta = client.get("/api/config")
    assert resposta.status_code == 200
    assert resposta.json() == {"tarifa_kwh": "1.27", "manutencao_mensal": "8.50"}
