"""Integration smoke tests — hit the real BCB API.

Run with: pytest -m integration
These may be slow and can fail if BCB is down.
"""

from __future__ import annotations

import json

import pytest

from capivara_mcp.tools.atividade import get_atividade_economica
from capivara_mcp.tools.expectativas import (
    get_expectativas_inflacao12m,
    get_expectativas_mensais,
    get_expectativas_mercado,
    get_expectativas_selic,
    get_expectativas_top5,
)
from capivara_mcp.tools.inflacao import get_inflacao
from capivara_mcp.tools.ptax import get_ptax
from capivara_mcp.tools.selic import get_selic
from capivara_mcp.tools.taxa_juros import get_taxa_juros


@pytest.mark.integration
class TestIntegrationBCB:
    def test_ptax_usd(self):
        result = get_ptax(moeda="USD", data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "cotacoes" in data
        assert len(data["cotacoes"]) > 0
        first = data["cotacoes"][0]
        assert "cotacao_compra" in first
        assert "cotacao_venda" in first

    def test_selic(self):
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "selic" in data
        assert len(data["selic"]) > 0

    def test_inflacao_ipca(self):
        result = get_inflacao(indice="IPCA", data_inicio="2024-06-01", data_fim="2024-12-31")
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "valores" in data
        assert data["indice"] == "IPCA"

    def test_inflacao_cdi(self):
        result = get_inflacao(indice="CDI", data_inicio="2024-06-01", data_fim="2024-12-31")
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "valores" in data
        assert data["indice"] == "CDI"

    def test_atividade_pib(self):
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2024-01-01", data_fim="2024-12-31")
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "valores" in data
        assert data["indicador"] == "PIB mensal"

    def test_expectativas_selic_anuais(self):
        result = get_expectativas_mercado(indicador="Selic", top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert len(data["expectativas"]) <= 3

    def test_expectativas_mensais_ipca(self):
        result = get_expectativas_mensais(indicador="IPCA", top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert data["frequencia"] == "mensal"

    def test_expectativas_selic_reuniao(self):
        result = get_expectativas_selic(top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert data["frequencia"] == "por_reuniao"

    def test_expectativas_inflacao12m(self):
        result = get_expectativas_inflacao12m(indicador="IPCA", top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert data["horizonte"] == "12_meses"

    def test_expectativas_top5(self):
        result = get_expectativas_top5(indicador="IPCA", top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert data["tipo"] == "top5_anual"

    def test_taxa_juros(self):
        result = get_taxa_juros(mes="Jan-2025", top=5)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "taxas" in data
