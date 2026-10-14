from decimal import Decimal as D
import pytest
from app.billing import calcular_rateio


def test_uma_sessao_t01():
    r = calcular_rateio([D("18.5")])
    assert (r.custo_energia, r.taxa_manutencao, r.total) == (D("16.65"), D("5.00"), D("21.65"))


def test_uma_sessao_t02():
    assert calcular_rateio([D("24")]).total == D("26.60")


def test_duas_sessoes_mes_taxa_uma_vez_t03():
    r = calcular_rateio([D("10"), D("15")])
    assert r.energia_kwh == D("25") and r.total == D("27.50") and r.taxa_manutencao == D("5.00")


def test_interrompida_consumo_efetivo_t04():
    assert calcular_rateio([D("4")]).total == D("8.60")


def test_sem_consumo_t05():
    assert calcular_rateio([]).total == D("0.00")


def test_arredondamento_decimal():
    assert calcular_rateio([D("0.005")], D("1.00"), D("0")).total == D("0.01")


def test_rejeita_negativos():
    with pytest.raises(ValueError):
        calcular_rateio([D("-1")])
