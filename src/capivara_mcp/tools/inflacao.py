"""Tool para consulta de índices de inflação (IPCA e IGP-M) do Banco Central."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import date, timedelta

import pandas as pd
import requests
from bcb import sgs

from capivara_mcp.tools._validation import erro_json, parse_date, validate_date_range

logger = logging.getLogger("capivara-mcp.inflacao")

_MAX_DAYS = 1825  # ~5 anos (dados mensais)
_API_TIMEOUT_SECONDS = 30


# Códigos das séries no SGS
_SERIES = {
    "IPCA": 433,
    "IGP-M": 189,
}


def _fetch_inflacao(indice: str, codigo: int, dt_inicio: date, dt_fim: date) -> pd.DataFrame:
    """Busca índice de inflação na API SGS do BCB."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            sgs.get,
            {indice: codigo},
            start=dt_inicio.strftime("%Y-%m-%d"),
            end=dt_fim.strftime("%Y-%m-%d"),
        )
        return future.result(timeout=_API_TIMEOUT_SECONDS)  # type: ignore[return-value]  # sgs.get returns DataFrame for dict input


def get_inflacao(
    indice: str = "IPCA",
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
    """Consulta índices de inflação (IPCA ou IGP-M) do Banco Central do Brasil.

    Retorna os valores mensais do índice de inflação escolhido para o período.
    Dados obtidos do SGS (Sistema Gerenciador de Séries Temporais) do BCB.

    Args:
        indice: Índice de inflação: "IPCA" ou "IGP-M". Padrão: "IPCA".
        data_inicio: Data inicial no formato YYYY-MM-DD. Padrão: 365 dias atrás.
        data_fim: Data final no formato YYYY-MM-DD. Padrão: hoje.

    Returns:
        JSON com os valores mensais do índice no período.
    """
    logger.info("get_inflacao chamado: indice=%s, data_inicio=%s, data_fim=%s", indice, data_inicio, data_fim)

    indice_upper = indice.upper()
    if indice_upper not in _SERIES:
        return json.dumps(
            {"erro": f"Índice '{indice}' não suportado. Use 'IPCA' ou 'IGP-M'."},
            ensure_ascii=False,
        )

    hoje = date.today()

    if data_fim:
        parsed = parse_date(data_fim, "data_fim")
        if isinstance(parsed, str):
            return parsed
        dt_fim = parsed
    else:
        dt_fim = hoje

    if data_inicio:
        parsed = parse_date(data_inicio, "data_inicio")
        if isinstance(parsed, str):
            return parsed
        dt_inicio = parsed
    else:
        dt_inicio = dt_fim - timedelta(days=365)

    range_err = validate_date_range(dt_inicio, dt_fim, _MAX_DAYS)
    if range_err:
        return range_err

    try:
        codigo = _SERIES[indice_upper]
        df: pd.DataFrame = _fetch_inflacao(indice_upper, codigo, dt_inicio, dt_fim)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhum dado de {indice_upper} encontrado no período informado."},
                ensure_ascii=False,
            )

        df.index.name = "data"
        df = df.reset_index()
        df["data"] = df["data"].dt.strftime("%Y-%m-%d")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {
                "indice": indice_upper,
                "periodo": {"inicio": str(dt_inicio), "fim": str(dt_fim)},
                "valores": registros,
            },
            ensure_ascii=False,
        )

    except FuturesTimeoutError:
        return erro_json(f"Tempo limite excedido ao consultar {indice_upper} na API do BCB. Tente novamente.")
    except requests.ConnectionError:
        return erro_json("Não foi possível conectar à API do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar inflação: indice=%s", indice_upper)
        return erro_json(f"Erro inesperado ao consultar {indice_upper}. Verifique os parâmetros.")
