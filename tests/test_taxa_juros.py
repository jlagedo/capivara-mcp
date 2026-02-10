"""Tests for taxa_juros.py — mock _fetch_taxa_juros for unit tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pandas as pd

from capivara_mcp.tools.taxa_juros import get_taxa_juros
from tests.conftest import make_taxa_juros_df

_PATCH = "capivara_mcp.tools.taxa_juros._fetch_taxa_juros"


class TestGetTaxaJurosSuccess:
    @patch(_PATCH)
    def test_basic_success(self, mock_fetch):
        mock_fetch.return_value = make_taxa_juros_df(n=3)
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        assert data["mes"] == "Jan-2025"
        assert "taxas" in data
        assert len(data["taxas"]) == 3

    @patch(_PATCH)
    def test_with_modalidade_filter(self, mock_fetch):
        mock_fetch.return_value = make_taxa_juros_df(n=2)
        result = get_taxa_juros(mes="Jan-2025", modalidade="CHEQUE ESPECIAL")
        data = json.loads(result)
        assert data["mes"] == "Jan-2025"
        assert len(data["taxas"]) == 2

    @patch(_PATCH)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_taxa_juros_df(n=1)
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        record = data["taxas"][0]
        assert "instituicao" in record
        assert "modalidade" in record
        assert "taxa_mensal" in record
        assert "taxa_anual" in record
        assert "cnpj8" in record
        # CamelCase originals should not be present
        assert "InstituicaoFinanceira" not in record
        assert "TaxaJurosAoMes" not in record

    @patch(_PATCH)
    def test_returns_json_string(self, mock_fetch):
        mock_fetch.return_value = make_taxa_juros_df()
        result = get_taxa_juros(mes="Jan-2025")
        assert isinstance(result, str)
        json.loads(result)


class TestGetTaxaJurosEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "Jan-2025" in data["erro"]

    @patch(_PATCH)
    def test_empty_with_modalidade(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_taxa_juros(mes="Jan-2025", modalidade="INEXISTENTE")
        data = json.loads(result)
        assert "erro" in data
        assert "INEXISTENTE" in data["erro"]


class TestGetTaxaJurosValidation:
    def test_invalid_mes_format_lowercase(self):
        result = get_taxa_juros(mes="jan-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "formato" in data["erro"].lower()

    def test_invalid_mes_format_numeric(self):
        result = get_taxa_juros(mes="01-2025")
        data = json.loads(result)
        assert "erro" in data

    def test_invalid_mes_format_full_month(self):
        result = get_taxa_juros(mes="January-2025")
        data = json.loads(result)
        assert "erro" in data

    def test_invalid_mes_format_no_year(self):
        result = get_taxa_juros(mes="Jan")
        data = json.loads(result)
        assert "erro" in data


class TestGetTaxaJurosErrors:
    @patch(_PATCH, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_taxa_juros(mes="Jan-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
