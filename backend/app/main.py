"""API FastAPI do EV ChargeOps: rateio e IA integrada (etapas 1 e 2)."""
from datetime import datetime, timezone
from decimal import Decimal
import os
import re
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .billing import calcular_rateio
from .intelligence import previsao_demanda, anomalias_sessoes, recomendacoes_operacionais
from .database import get_db
from .models import Carregador, Sessao, Usuario
from .schemas import CarregadorSaida, FaturaSaida, SessaoEntrada, SessaoSaida, UsuarioSaida

app = FastAPI(title="EV ChargeOps — Sprint 2", version="1.0.0")
# Interface servida localmente na porta 5173 (localhost/127.0.0.1).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")


def validar_periodo(periodo: str) -> str:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo):
        raise HTTPException(status_code=422, detail="Período deve ser AAAA-MM, como 2026-10")
    return periodo


def inicio_utc(data: datetime) -> datetime:
    # SQLite descarta TZ em DateTime; nosso contrato considera os dados armazenados em UTC.
    if data.tzinfo is None:
        return data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


def pertence_ao_periodo(sessao: Sessao, periodo: str) -> bool:
    # Política de negócio: sessão atribuída ao mês LOCAL do seu início.
    return inicio_utc(sessao.inicio).astimezone(FUSO_LOCAL).strftime("%Y-%m") == periodo


def tarifa_atual() -> tuple[Decimal, Decimal]:
    tarifa = Decimal(os.getenv("TARIFA_KWH", "0.90"))
    manutencao = Decimal(os.getenv("MANUTENCAO_MENSAL", "5.00"))
    if tarifa < 0 or manutencao < 0:
        raise RuntimeError("Configuração de preços não pode ser negativa")
    return tarifa, manutencao


def serializar_sessao(s: Sessao) -> SessaoSaida:
    # Reconstrói a saída com timezone explícito mesmo em SQLite nos testes.
    return SessaoSaida(
        id=s.id, usuario_id=s.usuario_id, carregador_id=s.carregador_id,
        inicio=inicio_utc(s.inicio), fim=inicio_utc(s.fim),
        energia_kwh=s.energia_kwh, estado=s.estado,
        origem=s.origem, validado=s.validado,
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "versao": "sprint-2-final", "fonte": "dados_simulados"}


@app.get("/api/config")
def configuracao():
    """Mostra ao dashboard a tarifa real usada na apuração."""
    tarifa, manutencao = tarifa_atual()
    return {"tarifa_kwh": str(tarifa), "manutencao_mensal": str(manutencao)}


@app.get("/api/users", response_model=list[UsuarioSaida])
def usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


@app.get("/api/chargers", response_model=list[CarregadorSaida])
def carregadores(db: Session = Depends(get_db)):
    return db.scalars(select(Carregador).order_by(Carregador.id)).all()


@app.post("/api/sessions", response_model=SessaoSaida, status_code=201)
def registrar_sessao(dados: SessaoEntrada, db: Session = Depends(get_db)):
    if db.get(Sessao, dados.id):
        raise HTTPException(status_code=409, detail="ID de sessão já cadastrado")
    if not db.get(Usuario, dados.usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not db.get(Carregador, dados.carregador_id):
        raise HTTPException(status_code=404, detail="Carregador não encontrado")

    # Usamos instantes UTC, inclusive ao consultar dados gravados pelo SQLite de teste.
    inicio = inicio_utc(dados.inicio)
    fim = inicio_utc(dados.fim)
    existentes = db.scalars(select(Sessao).where(Sessao.carregador_id == dados.carregador_id)).all()
    for atual in existentes:
        if inicio < inicio_utc(atual.fim) and fim > inicio_utc(atual.inicio):
            raise HTTPException(status_code=409, detail="Conflito: carregador ocupado nesse intervalo")

    sessao = Sessao(
        **dados.model_dump(exclude={"inicio", "fim"}), inicio=inicio, fim=fim
    )
    db.add(sessao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflito ao persistir sessão") from None
    db.refresh(sessao)
    return serializar_sessao(sessao)


@app.get("/api/sessions", response_model=list[SessaoSaida])
def listar_sessoes(period: str | None = Query(None), db: Session = Depends(get_db)):
    if period:
        validar_periodo(period)
    sessoes = db.scalars(select(Sessao).order_by(Sessao.inicio, Sessao.id)).all()
    if period:
        sessoes = [s for s in sessoes if pertence_ao_periodo(s, period)]
    retorno = []
    for sessao in sessoes:
        retorno.append(serializar_sessao(sessao))
    return retorno


@app.get("/api/invoices", response_model=list[FaturaSaida])
def faturas(period: str = Query(..., description="Mês local AAAA-MM"), db: Session = Depends(get_db)):
    validar_periodo(period)
    tarifa, manutencao = tarifa_atual()
    todos = db.scalars(select(Sessao)).all()
    por_usuario: dict[str, list[Sessao]] = {}
    for s in todos:
        if pertence_ao_periodo(s, period):
            por_usuario.setdefault(s.usuario_id, []).append(s)
    resposta = []
    for u in db.scalars(select(Usuario).order_by(Usuario.id)).all():
        registros = por_usuario.get(u.id, [])
        validados = [s.energia_kwh for s in registros if s.validado and s.estado in ("concluida", "interrompida")]
        pendentes = len(registros) - len(validados)
        resumo = calcular_rateio(validados, tarifa, manutencao)
        resposta.append(FaturaSaida(
            periodo=period, usuario_id=u.id, usuario_nome=u.nome,
            sessoes_cobradas=resumo.sessoes_cobradas,
            sessoes_pendentes=pendentes,
            energia_kwh=resumo.energia_kwh, tarifa_kwh=tarifa,
            custo_energia=resumo.custo_energia,
            taxa_manutencao=resumo.taxa_manutencao,
            total=resumo.total,
            situacao="pendencia_para_revisao" if pendentes else ("com_consumo" if resumo.energia_kwh > 0 else "sem_consumo"),
        ))
    return resposta


# Ambos os modelos consomem a MESMA tabela de sessões usada no rateio.
def ler_sessoes_ia(db: Session) -> list[Sessao]:
    return list(db.scalars(select(Sessao).order_by(Sessao.inicio, Sessao.id)).all())


@app.get("/api/ai/forecast")
def prever_demanda(db: Session = Depends(get_db)):
    return previsao_demanda(ler_sessoes_ia(db))


@app.get("/api/ai/anomalies")
def detectar_anomalias(db: Session = Depends(get_db)):
    return anomalias_sessoes(ler_sessoes_ia(db))


@app.get("/api/ai/recommendations")
def recomendar_operacao(db: Session = Depends(get_db)):
    registros = ler_sessoes_ia(db)
    previsao = previsao_demanda(registros)
    anomalias = anomalias_sessoes(registros)
    return recomendacoes_operacionais(previsao, anomalias)
