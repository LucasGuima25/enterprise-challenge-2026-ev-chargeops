"""Regra pura de rateio (Sprint 1): energia x tarifa + manutenção mensal."""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Iterable

CENTAVO = Decimal("0.01")


def dinheiro(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Rateio:
    energia_kwh: Decimal
    custo_energia: Decimal
    taxa_manutencao: Decimal
    total: Decimal
    sessoes_cobradas: int


def calcular_rateio(
    consumos_kwh: Iterable[Decimal],
    tarifa_kwh: Decimal = Decimal("0.90"),
    manutencao_mensal: Decimal = Decimal("5.00"),
) -> Rateio:
    """Consolida consumo validado; taxa uma vez se houver consumo no mês."""
    consumos = list(consumos_kwh)
    if tarifa_kwh < 0 or manutencao_mensal < 0 or any(c < 0 for c in consumos):
        raise ValueError("Tarifa, manutenção e consumos não podem ser negativos")
    energia = sum(consumos, Decimal("0"))
    custo = dinheiro(energia * tarifa_kwh)
    taxa = dinheiro(manutencao_mensal) if energia > 0 else Decimal("0.00")
    return Rateio(
        energia_kwh=energia,
        custo_energia=custo,
        taxa_manutencao=taxa,
        total=dinheiro(custo + taxa),
        sessoes_cobradas=len(consumos),
    )
