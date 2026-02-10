"""Tests for expectativas.py — mock _fetch_* functions for unit tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pandas as pd

from capivara_mcp.tools.expectativas import (
    get_expectativas_inflacao12m,
    get_expectativas_mensais,
    get_expectativas_mercado,
    get_expectativas_selic,
    get_expectativas_top5,
)
from tests.conftest import (
    make_expectativas_df,
    make_expectativas_inflacao12m_df,
    make_expectativas_mensais_df,
    make_expectativas_selic_df,
    make_expectativas_top5_df,
)

_PATCH_ANUAIS = "capivara_mcp.tools.expectativas._fetch_expectativas"
_PATCH_MENSAIS = "capivara_mcp.tools.expectativas._fetch_expectativas_mensais"
_PATCH_SELIC = "capivara_mcp.tools.expectativas._fetch_expectativas_selic"
_PATCH_INFLACAO12M = "capivara_mcp.tools.expectativas._fetch_expectativas_inflacao12m"
_PATCH_TOP5 = "capivara_mcp.tools.expectativas._fetch_expectativas_top5"


# ---------------------------------------------------------------------------
# Expectativas anuais (existente)
# ---------------------------------------------------------------------------

class TestGetExpectativasSuccess:
    @patch(_PATCH_ANUAIS)
    def test_selic_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("Selic", n=3)
        result = get_expectativas_mercado(indicador="Selic", top=3)
        data = json.loads(result)
        assert data["indicador"] == "Selic"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH_ANUAIS)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("IPCA", n=2)
        result = get_expectativas_mercado(indicador="IPCA", top=5)
        data = json.loads(result)
        assert data["indicador"] == "IPCA"

    @patch(_PATCH_ANUAIS)
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

    @patch(_PATCH_ANUAIS)
    def test_datetime_converted_to_iso(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df("Selic", n=1)
        result = get_expectativas_mercado(indicador="Selic", top=1)
        data = json.loads(result)
        data_pesquisa = data["expectativas"][0]["data_pesquisa"]
        assert isinstance(data_pesquisa, str)
        assert "2025-01-10" == data_pesquisa

    @patch(_PATCH_ANUAIS)
    def test_returns_json_string(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_df()
        result = get_expectativas_mercado(indicador="Selic")
        assert isinstance(result, str)
        json.loads(result)


class TestGetExpectativasEmptyResponse:
    @patch(_PATCH_ANUAIS)
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
    @patch(_PATCH_ANUAIS, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH_ANUAIS, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH_ANUAIS, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_mercado(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]


# ---------------------------------------------------------------------------
# Expectativas mensais
# ---------------------------------------------------------------------------

class TestGetExpectativasMensaisSuccess:
    @patch(_PATCH_MENSAIS)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_mensais_df("IPCA", n=3)
        result = get_expectativas_mensais(indicador="IPCA", top=3)
        data = json.loads(result)
        assert data["indicador"] == "IPCA"
        assert data["frequencia"] == "mensal"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH_MENSAIS)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_mensais_df("IPCA", n=1)
        result = get_expectativas_mensais(indicador="IPCA", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "indicador" in record
        assert "data_pesquisa" in record
        assert "periodo_referencia" in record
        assert "media" in record

    @patch(_PATCH_MENSAIS)
    def test_datetime_converted_to_iso(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_mensais_df("IPCA", n=1)
        result = get_expectativas_mensais(indicador="IPCA", top=1)
        data = json.loads(result)
        data_pesquisa = data["expectativas"][0]["data_pesquisa"]
        assert isinstance(data_pesquisa, str)
        assert "2025-01-10" == data_pesquisa


class TestGetExpectativasMensaisEmptyResponse:
    @patch(_PATCH_MENSAIS)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_expectativas_mensais(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "IPCA" in data["erro"]


class TestGetExpectativasMensaisValidation:
    def test_unsupported_indicador(self):
        result = get_expectativas_mensais(indicador="SP500")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]


class TestGetExpectativasMensaisErrors:
    @patch(_PATCH_MENSAIS, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_mensais(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH_MENSAIS, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_mensais(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH_MENSAIS, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_mensais(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]


# ---------------------------------------------------------------------------
# Expectativas Selic (por reunião)
# ---------------------------------------------------------------------------

class TestGetExpectativasSelicSuccess:
    @patch(_PATCH_SELIC)
    def test_selic_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_selic_df(n=3)
        result = get_expectativas_selic(top=3)
        data = json.loads(result)
        assert data["indicador"] == "Selic"
        assert data["frequencia"] == "por_reuniao"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH_SELIC)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_selic_df(n=1)
        result = get_expectativas_selic(top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "data_pesquisa" in record
        assert "reuniao" in record
        assert "media" in record
        assert "mediana" in record

    @patch(_PATCH_SELIC)
    def test_datetime_converted_to_iso(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_selic_df(n=1)
        result = get_expectativas_selic(top=1)
        data = json.loads(result)
        data_pesquisa = data["expectativas"][0]["data_pesquisa"]
        assert isinstance(data_pesquisa, str)
        assert "2025-01-10" == data_pesquisa


class TestGetExpectativasSelicEmptyResponse:
    @patch(_PATCH_SELIC)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_expectativas_selic()
        data = json.loads(result)
        assert "erro" in data
        assert "Selic" in data["erro"]


class TestGetExpectativasSelicErrors:
    @patch(_PATCH_SELIC, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_selic()
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH_SELIC, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_selic()
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH_SELIC, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_selic()
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]


# ---------------------------------------------------------------------------
# Expectativas inflação 12 meses
# ---------------------------------------------------------------------------

class TestGetExpectativasInflacao12mSuccess:
    @patch(_PATCH_INFLACAO12M)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_inflacao12m_df("IPCA", n=3)
        result = get_expectativas_inflacao12m(indicador="IPCA", top=3)
        data = json.loads(result)
        assert data["indicador"] == "IPCA"
        assert data["horizonte"] == "12_meses"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH_INFLACAO12M)
    def test_has_suavizada_field(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_inflacao12m_df("IPCA", n=1)
        result = get_expectativas_inflacao12m(indicador="IPCA", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "suavizada" in record

    @patch(_PATCH_INFLACAO12M)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_inflacao12m_df("IPCA", n=1)
        result = get_expectativas_inflacao12m(indicador="IPCA", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "indicador" in record
        assert "data_pesquisa" in record
        assert "media" in record


class TestGetExpectativasInflacao12mEmptyResponse:
    @patch(_PATCH_INFLACAO12M)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_expectativas_inflacao12m(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "IPCA" in data["erro"]


class TestGetExpectativasInflacao12mValidation:
    def test_unsupported_indicador(self):
        result = get_expectativas_inflacao12m(indicador="Selic")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]

    def test_unsupported_indicador_pib(self):
        result = get_expectativas_inflacao12m(indicador="PIB Total")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]


class TestGetExpectativasInflacao12mErrors:
    @patch(_PATCH_INFLACAO12M, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_inflacao12m(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH_INFLACAO12M, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_inflacao12m(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH_INFLACAO12M, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_inflacao12m(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]


# ---------------------------------------------------------------------------
# Expectativas Top 5 anuais
# ---------------------------------------------------------------------------

class TestGetExpectativasTop5Success:
    @patch(_PATCH_TOP5)
    def test_ipca_success(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_top5_df("IPCA", n=3)
        result = get_expectativas_top5(indicador="IPCA", top=3)
        data = json.loads(result)
        assert data["indicador"] == "IPCA"
        assert data["tipo"] == "top5_anual"
        assert len(data["expectativas"]) == 3

    @patch(_PATCH_TOP5)
    def test_has_tipo_calculo_field(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_top5_df("IPCA", n=1)
        result = get_expectativas_top5(indicador="IPCA", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "tipo_calculo" in record

    @patch(_PATCH_TOP5)
    def test_column_renaming(self, mock_fetch):
        mock_fetch.return_value = make_expectativas_top5_df("Selic", n=1)
        result = get_expectativas_top5(indicador="Selic", top=1)
        data = json.loads(result)
        record = data["expectativas"][0]
        assert "indicador" in record
        assert "data_pesquisa" in record
        assert "periodo_referencia" in record
        assert "tipo_calculo" in record
        assert "media" in record


class TestGetExpectativasTop5EmptyResponse:
    @patch(_PATCH_TOP5)
    def test_empty_dataframe(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        result = get_expectativas_top5(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "IPCA" in data["erro"]


class TestGetExpectativasTop5Validation:
    def test_unsupported_indicador(self):
        result = get_expectativas_top5(indicador="SP500")
        data = json.loads(result)
        assert "erro" in data
        assert "não suportado" in data["erro"]


class TestGetExpectativasTop5Errors:
    @patch(_PATCH_TOP5, side_effect=httpx.TimeoutException("timeout"))
    def test_timeout(self, _):
        result = get_expectativas_top5(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "Tempo limite" in data["erro"]

    @patch(_PATCH_TOP5, side_effect=httpx.ConnectError("refused"))
    def test_connect_error(self, _):
        result = get_expectativas_top5(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "conectar" in data["erro"]

    @patch(_PATCH_TOP5, side_effect=RuntimeError("boom"))
    def test_unexpected_error(self, _):
        result = get_expectativas_top5(indicador="IPCA")
        data = json.loads(result)
        assert "erro" in data
        assert "inesperado" in data["erro"]
