"""Tests for inflacao.py — mock _fetch_inflacao for unit tests."""

from __future__ import annotations

import json
from concurrent.futures import TimeoutError as FuturesTimeoutError
from unittest.mock import patch

import pandas as pd
import requests

from capivara_mcp.tools.inflacao import get_inflacao
from tests.conftest import make_sgs_df

_PATCH = "capivara_mcp.tools.inflacao._fetch_inflacao"


class TestGetInflacaoSuccess:
    @patch(_PATCH)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"IPCA": 0.5}, n=3)
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert data["indice"] == "IPCA"
        assert "periodo" in data
        assert "valores" in data
        assert len(data["valores"]) == 3

    @patch(_PATCH)
    def test_igpm_success(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"IGP-M": 0.3}, n=2)
        result = get_inflacao(indice="IGP-M", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert data["indice"] == "IGP-M"
        assert len(data["valores"]) == 2

    @patch(_PATCH)
    def test_case_insensitive_indice(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"IPCA": 0.5}, n=1)
        result = get_inflacao(indice="ipca", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert data["indice"] == "IPCA"

    @patch(_PATCH)
    def test_records_have_expected_keys(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"IPCA": 0.5}, n=1)
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-01-31")
        data = json.loads(result)
        record = data["valores"][0]
        assert "data" in record
        assert "IPCA" in record

    @patch(_PATCH)
    def test_dates_formatted_as_iso(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"IPCA": 0.5}, n=1)
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-01-31")
        data = json.loads(result)
        assert data["valores"][0]["data"] == "2025-01-02"


class TestGetInflacaoEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "IPCA" in data["erro"]


class TestGetInflacaoValidation:
    def test_unsupported_indice(self):
        result = get_inflacao(indice="CPI")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]

    def test_invalid_data_inicio(self):
        result = get_inflacao(data_inicio="bad", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data

    def test_invalid_data_fim(self):
        result = get_inflacao(data_inicio="2025-01-02", data_fim="bad")
        data = json.loads(result)
        assert "erro" in data

    def test_start_after_end(self):
        result = get_inflacao(data_inicio="2025-02-01", data_fim="2025-01-01")
        data = json.loads(result)
        assert "erro" in data

    def test_exceeds_max_days(self):
        result = get_inflacao(data_inicio="2019-01-01", data_fim="2025-06-01")
        data = json.loads(result)
        assert "erro" in data
        assert "1825" in data["erro"]


class TestGetInflacaoErrors:
    @patch(_PATCH, side_effect=FuturesTimeoutError())
    def test_timeout(self, _):
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=requests.ConnectionError())
    def test_connection_error(self, _):
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_inflacao(indice="IPCA", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
