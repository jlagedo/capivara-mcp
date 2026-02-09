"""Tests for selic.py — mock _fetch_selic for unit tests."""

from __future__ import annotations

import json
from concurrent.futures import TimeoutError as FuturesTimeoutError
from unittest.mock import patch

import pandas as pd
import requests

from capivara_mcp.tools.selic import get_selic
from tests.conftest import make_sgs_df

_PATCH = "capivara_mcp.tools.selic._fetch_selic"


class TestGetSelicSuccess:
    @patch(_PATCH)
    def test_success_with_explicit_dates(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"selic_meta": 10.5, "selic_efetiva": 10.4})
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert data["periodo"]["inicio"] == "2025-01-02"
        assert data["periodo"]["fim"] == "2025-01-10"
        assert "selic" in data
        assert len(data["selic"]) == 5

    @patch(_PATCH)
    def test_records_have_expected_keys(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"selic_meta": 10.5, "selic_efetiva": 10.4}, n=1)
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-02")
        data = json.loads(result)
        record = data["selic"][0]
        assert "data" in record
        assert "selic_meta" in record
        assert "selic_efetiva" in record

    @patch(_PATCH)
    def test_dates_formatted_as_iso(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"selic_meta": 10.5, "selic_efetiva": 10.4}, n=1)
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-02")
        data = json.loads(result)
        assert data["selic"][0]["data"] == "2025-01-02"

    @patch(_PATCH)
    def test_returns_json_string(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"selic_meta": 10.5, "selic_efetiva": 10.4})
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        assert isinstance(result, str)
        json.loads(result)


class TestGetSelicEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data
        assert "Selic" in data["erro"]


class TestGetSelicValidation:
    def test_invalid_data_inicio(self):
        result = get_selic(data_inicio="bad", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data

    def test_invalid_data_fim(self):
        result = get_selic(data_inicio="2025-01-02", data_fim="bad")
        data = json.loads(result)
        assert "erro" in data

    def test_start_after_end(self):
        result = get_selic(data_inicio="2025-02-01", data_fim="2025-01-01")
        data = json.loads(result)
        assert "erro" in data

    def test_exceeds_max_days(self):
        result = get_selic(data_inicio="2024-01-01", data_fim="2025-06-01")
        data = json.loads(result)
        assert "erro" in data


class TestGetSelicErrors:
    @patch(_PATCH, side_effect=FuturesTimeoutError())
    def test_timeout(self, _):
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=requests.ConnectionError())
    def test_connection_error(self, _):
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_selic(data_inicio="2025-01-02", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
