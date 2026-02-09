"""Tests for ptax.py — mock _fetch_ptax for unit tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pandas as pd

from capivara_mcp.tools.ptax import get_ptax
from tests.conftest import make_ptax_df

_PATCH = "capivara_mcp.tools.ptax._fetch_ptax"


class TestGetPtaxSuccess:
    @patch(_PATCH)
    def test_success_with_explicit_dates(self, mock_fetch):
        mock_fetch.return_value = make_ptax_df(n=3)
        result = get_ptax(moeda="USD", data_inicio="2025-01-02", data_fim="2025-01-04")
        data = json.loads(result)
        assert data["moeda"] == "USD"
        assert data["periodo"]["inicio"] == "2025-01-02"
        assert data["periodo"]["fim"] == "2025-01-04"
        assert len(data["cotacoes"]) == 3

    @patch(_PATCH)
    def test_cotacoes_have_expected_keys(self, mock_fetch):
        mock_fetch.return_value = make_ptax_df(n=1)
        result = get_ptax(moeda="EUR", data_inicio="2025-01-02", data_fim="2025-01-02")
        data = json.loads(result)
        cotacao = data["cotacoes"][0]
        assert "cotacao_compra" in cotacao
        assert "cotacao_venda" in cotacao
        assert "data_hora" in cotacao
        assert "tipo_boletim" in cotacao

    @patch(_PATCH)
    def test_datetime_converted_to_iso_string(self, mock_fetch):
        mock_fetch.return_value = make_ptax_df(n=1)
        result = get_ptax(data_inicio="2025-01-02", data_fim="2025-01-02")
        data = json.loads(result)
        data_hora = data["cotacoes"][0]["data_hora"]
        assert isinstance(data_hora, str)
        assert "2025-01-02" in data_hora

    @patch(_PATCH)
    def test_returns_json_string(self, mock_fetch):
        mock_fetch.return_value = make_ptax_df()
        result = get_ptax(data_inicio="2025-01-02", data_fim="2025-01-04")
        assert isinstance(result, str)
        json.loads(result)  # should not raise


class TestGetPtaxEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_ptax(moeda="XYZ", data_inicio="2025-01-02", data_fim="2025-01-04")
        data = json.loads(result)
        assert "erro" in data
        assert "XYZ" in data["erro"]


class TestGetPtaxValidation:
    def test_invalid_data_inicio(self):
        result = get_ptax(data_inicio="bad-date", data_fim="2025-01-04")
        data = json.loads(result)
        assert "erro" in data
        assert "data_inicio" in data["erro"]

    def test_invalid_data_fim(self):
        result = get_ptax(data_inicio="2025-01-02", data_fim="31-12-2025")
        data = json.loads(result)
        assert "erro" in data
        assert "data_fim" in data["erro"]

    def test_start_after_end(self):
        result = get_ptax(data_inicio="2025-02-01", data_fim="2025-01-01")
        data = json.loads(result)
        assert "erro" in data

    def test_exceeds_max_days(self):
        result = get_ptax(data_inicio="2024-01-01", data_fim="2025-06-01")
        data = json.loads(result)
        assert "erro" in data
        assert "365" in data["erro"]


class TestGetPtaxErrors:
    @patch(_PATCH, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_ptax(data_inicio="2025-01-02", data_fim="2025-01-04")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_ptax(data_inicio="2025-01-02", data_fim="2025-01-04")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_ptax(data_inicio="2025-01-02", data_fim="2025-01-04")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
