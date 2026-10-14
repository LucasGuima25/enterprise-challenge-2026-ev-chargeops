"""IA explicável integrada às sessões do EV ChargeOps.

Todos os resultados são simulações educacionais. Não há telemetria GoodWe real.
As funções recebem sessões consultadas no mesmo banco usado pelo rateio.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import median
from zoneinfo import ZoneInfo

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from .models import Sessao

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
SEMENTE = 42
HORIZONTE = 7
MIN_DIAS = 35
MIN_SESSOES = 25


def utc(data: datetime) -> datetime:
    # DateTime SQLite pode retornar sem tzinfo. A base armazena UTC.
    return data.replace(tzinfo=timezone.utc) if data.tzinfo is None else data.astimezone(timezone.utc)


def sessoes_aproveitaveis(registros: list[Sessao]) -> list[Sessao]:
    """Mesma regra de elegibilidade do cálculo de rateio da Etapa 1."""
    return [
        s for s in registros
        if s.validado and s.estado in ("concluida", "interrompida")
        and float(s.energia_kwh) >= 0 and utc(s.fim) > utc(s.inicio)
    ]


def serie_diaria(registros: list[Sessao]) -> tuple[list[date], list[float]]:
    """Agrupa energia pelo DIA LOCAL do início, incluindo dias sem sessões."""
    somas = defaultdict(float)
    for sessao in sessoes_aproveitaveis(registros):
        dia = utc(sessao.inicio).astimezone(SAO_PAULO).date()
        somas[dia] += float(sessao.energia_kwh)
    if not somas:
        return [], []
    inicio = min(somas)
    fim = max(somas)
    # Proteção de recurso: até um ano de observações recentes.
    inicio = max(inicio, fim - timedelta(days=364))
    datas = [inicio + timedelta(days=i) for i in range((fim - inicio).days + 1)]
    valores = [round(somas.get(d, 0.0), 3) for d in datas]
    return datas, valores


def atributos_dia(dia: date, indice: int, historico: list[float]) -> list[float]:
    """Utiliza somente dias anteriores ao alvo; evita vazamento do próprio dia."""
    dow = dia.weekday()
    anteriores = historico[indice - 7:indice]
    return [
        float(indice),
        float(np.sin(2 * np.pi * dow / 7)),
        float(np.cos(2 * np.pi * dow / 7)),
        float(dow >= 5),
        float(historico[indice - 1]),
        float(historico[indice - 7]),
        float(np.mean(anteriores)),
    ]


def previsao_demanda(registros: list[Sessao]) -> dict:
    datas, valores = serie_diaria(registros)
    validas = sessoes_aproveitaveis(registros)
    base = {"status": "dados_insuficientes", "fonte": "sessoes_validadas_do_banco",
            "modelo": "RandomForestRegressor", "horizonte_dias": HORIZONTE,
            "sessoes_analisadas": len(validas), "dias_historicos": len(datas),
            "aviso": "Apenas dados simulados; não representa previsão para equipamento real."}
    if len(datas) < MIN_DIAS:
        return {**base, "mensagem": f"São necessários pelo menos {MIN_DIAS} dias históricos (incluindo dias sem sessões).",
                "metricas": None, "previsoes": [], "limiar_pico_kwh": None}

    X = [atributos_dia(datas[i], i, valores) for i in range(7, len(datas))]
    y = valores[7:]
    teste_n = max(7, int(len(X) * 0.2))
    corte = len(X) - teste_n
    if corte < 14:
        return {**base, "mensagem": "Amostra insuficiente para treino/teste cronológicos.",
                "metricas": None, "previsoes": [], "limiar_pico_kwh": None}

    # Validação temporal: treina apenas no começo da série; avalia dias posteriores.
    # No teste, lags refletem consumo REAL de dias anteriores, conhecido no instante
    # de cada previsão: avaliação um-passo-à-frente (walk-forward), não multietapas.
    validacao = RandomForestRegressor(n_estimators=80, max_depth=8,
                                      min_samples_leaf=2, random_state=SEMENTE, n_jobs=1)
    validacao.fit(X[:corte], y[:corte])
    pred_teste = np.maximum(0.0, validacao.predict(X[corte:]))
    mae_modelo = mean_absolute_error(y[corte:], pred_teste)
    mae_base = mean_absolute_error(y[corte:], [X[i][6] for i in range(corte, len(X))])

    final = RandomForestRegressor(n_estimators=80, max_depth=8,
                                  min_samples_leaf=2, random_state=SEMENTE, n_jobs=1)
    final.fit(X, y)
    projetado = list(valores)
    previsoes = []
    limiar = float(np.quantile(valores, 0.75))
    for passo in range(1, HORIZONTE + 1):
        alvo = datas[-1] + timedelta(days=passo)
        x_futuro = atributos_dia(alvo, len(projetado), projetado)
        kwh = max(0.0, float(final.predict([x_futuro])[0]))
        projetado.append(kwh)  # recursividade: usa previsão em lags subsequentes
        previsoes.append({"data": alvo.isoformat(), "kwh_previstos": round(kwh, 3),
                          "acima_limiar_historico": bool(limiar > 0 and kwh > limiar)})

    return {**base, "status": "ok", "mensagem": "Treino e inferência concluídos.",
            "periodo_historico": {"inicio": datas[0].isoformat(), "fim": datas[-1].isoformat()},
            "metricas": {"treino_dias": corte, "teste_dias": teste_n,
                         "mae_modelo_kwh": round(float(mae_modelo), 3),
                         "mae_baseline_media_7d_kwh": round(float(mae_base), 3),
                         "supera_baseline": bool(mae_modelo < mae_base),
                         "validacao": "cronologica_um_passo_a_frente"},
            "limiar_pico_kwh": round(limiar, 3), "previsoes": previsoes}


def anomalias_sessoes(registros: list[Sessao]) -> dict:
    validas = sessoes_aproveitaveis(registros)
    base = {"status": "dados_insuficientes", "fonte": "sessoes_validadas_do_banco",
            "modelo": "IsolationForest", "sessoes_analisadas": len(validas),
            "aviso": "Anomalia estatística não é prova de fraude, falha elétrica ou defeito."}
    if len(validas) < MIN_SESSOES:
        return {**base, "mensagem": f"Necessárias pelo menos {MIN_SESSOES} sessões validadas.",
                "total_anomalias": 0, "anomalias": []}

    entradas = []
    informacoes = []
    for sessao in validas:
        inicio_local = utc(sessao.inicio).astimezone(SAO_PAULO)
        horas = (utc(sessao.fim) - utc(sessao.inicio)).total_seconds() / 3600
        energia = float(sessao.energia_kwh)
        potencia = energia / horas
        # Atributos sem dados de fatura nem status de pagamento.
        entradas.append([horas, energia, potencia, inicio_local.hour,
                         inicio_local.weekday(), int(sessao.estado == "interrompida")])
        informacoes.append((sessao, inicio_local, horas, energia, potencia))
    modelo = IsolationForest(n_estimators=100, contamination=0.08,
                             random_state=SEMENTE, n_jobs=1)
    modelo.fit(entradas)
    marcacoes = modelo.predict(entradas)
    scores = modelo.decision_function(entradas)
    energias = [x[3] for x in informacoes]
    horas_lista = [x[2] for x in informacoes]
    potencias = [x[4] for x in informacoes]
    med_energia = median(energias)
    med_horas = median(horas_lista)
    med_potencia = median(potencias)
    registros_anomalos = []
    for (sessao, hora_local, duracao, energia, potencia), marca, score in zip(informacoes, marcacoes, scores):
        if marca != -1:
            continue
        sinais = []
        if energia > max(1.0, med_energia) * 1.6:
            sinais.append("energia elevada comparada à mediana")
        if energia < max(0.5, med_energia * 0.35):
            sinais.append("energia baixa comparada à mediana")
        if duracao > max(0.5, med_horas) * 1.6:
            sinais.append("duração acima do padrão")
        if potencia > max(0.5, med_potencia) * 1.6:
            sinais.append("potência média elevada comparada à mediana")
        if sessao.estado == "interrompida":
            sinais.append("sessão interrompida")
        if not sinais:
            sinais.append("combinação atípica de consumo, duração e horário")
        registros_anomalos.append({
            "sessao_id": sessao.id, "usuario_id": sessao.usuario_id,
            "inicio_local": hora_local.isoformat(), "energia_kwh": round(energia, 3),
            "duracao_horas": round(duracao, 3), "potencia_media_kw": round(potencia, 3),
            "score": round(float(score), 5),
            "indicadores_descritivos": sinais,
        })
    registros_anomalos.sort(key=lambda item: (item["score"], item["sessao_id"]))
    return {**base, "status": "ok", "mensagem": "Detecção estatística concluída.",
            "total_anomalias": len(registros_anomalos), "anomalias": registros_anomalos}


def recomendacoes_operacionais(previsao: dict, anomalias: dict) -> dict:
    """Regras de negócio alimentadas pelo resultado REAL dos dois modelos."""
    saidas = []
    if previsao["status"] != "ok":
        saidas.append({"tipo": "dados", "prioridade": "media",
                       "mensagem": "Amplie o histórico diário para habilitar previsão de demanda.",
                       "evidencia": f"Dias disponíveis: {previsao['dias_historicos']}; mínimo: {MIN_DIAS}."})
    else:
        if not previsao["metricas"]["supera_baseline"]:
            saidas.append({"tipo": "validacao", "prioridade": "alta",
                           "mensagem": "O modelo não superou a média histórica de 7 dias; não automatizar decisões de agendamento.",
                           "evidencia": (f"MAE modelo {previsao['metricas']['mae_modelo_kwh']} kWh; "
                                         f"MAE baseline {previsao['metricas']['mae_baseline_media_7d_kwh']} kWh.")})
        picos = [p for p in previsao["previsoes"] if p["acima_limiar_historico"]]
        if picos:
            topo = max(picos, key=lambda p: p["kwh_previstos"])
            saidas.append({"tipo": "demanda", "prioridade": "media",
                           "mensagem": f"Considere incentivar o uso fora do pico previsto para {topo['data']}.",
                           "evidencia": f"Previsão {topo['kwh_previstos']} kWh; P75 histórico {previsao['limiar_pico_kwh']} kWh."})
        else:
            saidas.append({"tipo": "demanda", "prioridade": "baixa",
                           "mensagem": "Não foram previstos dias acima do limiar histórico no horizonte avaliado.",
                           "evidencia": f"Limiar P75: {previsao['limiar_pico_kwh']} kWh; horizonte {HORIZONTE} dias."})
    if anomalias["status"] != "ok":
        saidas.append({"tipo": "qualidade", "prioridade": "media",
                       "mensagem": "Amplie as sessões validadas para habilitar detecção de anomalias.",
                       "evidencia": f"Sessões disponíveis: {anomalias['sessoes_analisadas']}; mínimo: {MIN_SESSOES}."})
    elif anomalias["total_anomalias"]:
        mais_atipica = anomalias["anomalias"][0]
        saidas.append({"tipo": "revisao", "prioridade": "alta",
                       "mensagem": "Solicite revisão humana das sessões atípicas antes de tomar decisões.",
                       "evidencia": (f"{anomalias['total_anomalias']} sinalizadas; "
                                     f"mais atípica: {mais_atipica['sessao_id']}, score {mais_atipica['score']}.")})
    else:
        saidas.append({"tipo": "revisao", "prioridade": "baixa",
                       "mensagem": "Nenhuma sessão atípica sinalizada neste conjunto.",
                       "evidencia": f"Sessões analisadas: {anomalias['sessoes_analisadas']}."})
    return {"status": "ok" if previsao["status"] == anomalias["status"] == "ok" else "parcial",
            "fonte": "resultados_dos_modelos_sobre_sessoes_do_banco",
            "recomendacoes": saidas,
            "aviso": "Orientações indicativas para operador humano; não acionam carregadores."}
