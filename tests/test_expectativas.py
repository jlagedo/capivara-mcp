"""Tests for expectativas.py — mock _fetch_expectativas for unit tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pandas as pd

from capivara_mcp.tools.expectativas import get_expectativas_mercado
from tests.conftest import make_expectativas_df

_PATCH = "capivara_mcp.tools.expectativas._fetch_expectativas"


class TestGetExpectativasSuccess:
    @patch(_PATCH)
    def test_selic_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("Selic", n=3)
        result = get_expectativas_mercado(indicador="Selic", top=3)
        data = json.loads(result)
        assert data["indicador"] == "Selic"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("IPCA", n=2)
        result = get_expectativas_mercado(indicador="IPCA", top=5)
        data = json.loads(result)
        assert data["indicador"] == "IPCA"

    @patch(_PATCH)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("Selic", n=1)
        result = get_expectativas_mercado(indicador="Selic", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "indicador" in record
        assert "data_pesquisa" in record
        assert "periodo_referencia" in record
        assert "media" in record
        assert "mediana" in record
        assert "minimo" in record
        assert "maximo" in record
        # CamelCase originals should not be present
        assert "Indicador" not in record
        assert "Data" not in record

    @patch(_PATCH)
    def test_datetime_converted_to_iso(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("Selic", n=1)
        result = get_expectativas_mercado(indicador="Selic", top=1)
        data = json.loads(result)
        data_pesquisa = data["expectativas"][0]["data_pesquisa"]
        assert isinstance(data_pesquisa, str)
        assert "2025-01-10" == data_pesquisa

    @patch(_PATCH)
    def test_returns_json_string(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df()
        result = get_expectativas_mercado(indicador="Selic")
        assert isinstance(result, str)
        json.loads(result)


class TestGetExpectativasEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "Selic" in data["erro"]


class TestGetExpectativasValidation:
    def test_unsupported_indicador(self):
        result = get_expectativas_mercado(indicador="SP500")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]
        assert "SP500" in data["erro"]

    def test_unsupported_indicador_lists_valid_options(self):
        result = get_expectativas_mercado(indicador="invalid")
        data = json.loads(result)
        # Should list some valid indicators in the error
        assert "Selic" in data["erro"]
        assert "IPCA" in data["erro"]


class TestGetExpectativasErrors:
    @patch(_PATCH, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
