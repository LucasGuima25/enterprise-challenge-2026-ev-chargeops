"""Contratos públicos: entradas invalidadas não podem gerar sessões faturadas."""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoSessao = Literal["concluida", "interrompida", "falha_comunicacao"]
Origem = Literal["simulado", "manual"]


class SessaoEntrada(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    usuario_id: str = Field(min_length=1, max_length=20)
    carregador_id: str = Field(min_length=1, max_length=20)
    inicio: datetime
    fim: datetime
    energia_kwh: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    estado: EstadoSessao
    origem: Origem = "simulado"
    validado: bool = True

    @model_validator(mode="after")
    def validar_periodo_e_estado(self):
        if (self.inicio.tzinfo is None or self.inicio.utcoffset() is None
                or self.fim.tzinfo is None or self.fim.utcoffset() is None):
            raise ValueError("Início e fim precisam informar o fuso horário, como -03:00")
        if self.fim <= self.inicio:
            raise ValueError("Fim deve ocorrer depois do início")
        if self.estado == "falha_comunicacao" and self.validado:
            raise ValueError("Falha de comunicação deve permanecer pendente (validado=false)")
        return self


class SessaoSaida(SessaoEntrada):
    model_config = ConfigDict(from_attributes=True)


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nome: str
    email: str
    tipo: str
    unidade_id: str


class CarregadorSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    modelo: str
    localizacao: str
    estado: str
    potencia_max_kw: Decimal


class FaturaSaida(BaseModel):
    periodo: str
    usuario_id: str
    usuario_nome: str
    sessoes_cobradas: int
    sessoes_pendentes: int
    energia_kwh: Decimal
    tarifa_kwh: Decimal
    custo_energia: Decimal
    taxa_manutencao: Decimal
    total: Decimal
    situacao: str
