"""Tests for atividade.py — mock _fetch_atividade for unit tests."""

from __future__ import annotations

import json
from concurrent.futures import TimeoutError as FuturesTimeoutError
from unittest.mock import patch

import pandas as pd
import requests

from capivara_mcp.tools.atividade import get_atividade_economica
from tests.conftest import make_sgs_df

_PATCH = "capivara_mcp.tools.atividade._fetch_atividade"


class TestGetAtividadeSuccess:
    @patch(_PATCH)
    def test_pib_mensal_success(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"PIB mensal": 150.0}, n=3)
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert data["indicador"] == "PIB mensal"
        assert "periodo" in data
        assert "valores" in data
        assert len(data["valores"]) == 3

    @patch(_PATCH)
    def test_divida_pib_success(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"Dívida bruta/PIB": 75.0}, n=2)
        result = get_atividade_economica(indicador="Dívida bruta/PIB", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert data["indicador"] == "Dívida bruta/PIB"
        assert len(data["valores"]) == 2

    @patch(_PATCH)
    def test_resultado_primario_success(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"Resultado primário": -10.0}, n=4)
        result = get_atividade_economica(indicador="Resultado primário", data_inicio="2025-01-02", data_fim="2025-06-01")
        data = json.loads(result)
        assert data["indicador"] == "Resultado primário"
        assert len(data["valores"]) == 4

    @patch(_PATCH)
    def test_records_have_expected_keys(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"PIB mensal": 150.0}, n=1)
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-01-31")
        data = json.loads(result)
        record = data["valores"][0]
        assert "data" in record
        assert "PIB mensal" in record

    @patch(_PATCH)
    def test_dates_formatted_as_iso(self, mock_fetch):
        mock_fetch.return_value = make_sgs_df({"PIB mensal": 150.0}, n=1)
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-01-31")
        data = json.loads(result)
        assert data["valores"][0]["data"] == "2025-01-02"


class TestGetAtividadeEmptyResponse:
    @patch(_PATCH)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "PIB mensal" in data["erro"]


class TestGetAtividadeValidation:
    def test_unsupported_indicador(self):
        result = get_atividade_economica(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]

    def test_invalid_data_inicio(self):
        result = get_atividade_economica(data_inicio="bad", data_fim="2025-01-10")
        data = json.loads(result)
        assert "erro" in data

    def test_invalid_data_fim(self):
        result = get_atividade_economica(data_inicio="2025-01-02", data_fim="bad")
        data = json.loads(result)
        assert "erro" in data

    def test_start_after_end(self):
        result = get_atividade_economica(data_inicio="2025-02-01", data_fim="2025-01-01")
        data = json.loads(result)
        assert "erro" in data

    def test_exceeds_max_days(self):
        result = get_atividade_economica(data_inicio="2019-01-01", data_fim="2025-06-01")
        data = json.loads(result)
        assert "erro" in data
        assert "1825" in data["erro"]


class TestGetAtividadeErrors:
    @patch(_PATCH, side_effect=FuturesTimeoutError())
    def test_timeout(self, _):
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH, side_effect=requests.ConnectionError())
    def test_connection_error(self, _):
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_atividade_economica(indicador="PIB mensal", data_inicio="2025-01-02", data_fim="2025-03-01")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
