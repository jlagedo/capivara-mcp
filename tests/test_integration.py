"""Integration smoke tests — hit the real BCB API.

Run with: pytest -m integration
These may be slow and can fail if BCB is down.
"""

from __future__ import annotations

import json

import pytest

from capivara_mcp.tools.expectativas import get_expectativas_mercado
from capivara_mcp.tools.inflacao import get_inflacao
from capivara_mcp.tools.ptax import get_ptax
from capivara_mcp.tools.selic import get_selic


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

    def test_expectativas_selic(self):
        result = get_expectativas_mercado(indicador="Selic", top=3)
        data = json.loads(result)
        assert "erro" not in data, f"Unexpected error: {data}"
        assert "expectativas" in data
        assert len(data["expectativas"]) <= 3
