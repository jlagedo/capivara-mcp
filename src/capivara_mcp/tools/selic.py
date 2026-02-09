"""Tool para consulta da taxa Selic (meta e efetiva) do Banco Central."""

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

logger = logging.getLogger("capivara-mcp.selic")

_MAX_DAYS = 365
_API_TIMEOUT_SECONDS = 30


# Códigos das séries no SGS
_SERIES = {
    "meta": 432,
    "efetiva": 11,
}


def _fetch_selic(dt_inicio: date, dt_fim: date) -> pd.DataFrame:
    """Busca taxas Selic na API SGS do BCB."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            sgs.get,
            {"selic_meta": _SERIES["meta"], "selic_efetiva": _SERIES["efetiva"]},
            start=dt_inicio.strftime("%Y-%m-%d"),
            end=dt_fim.strftime("%Y-%m-%d"),
        )
        return future.result(timeout=_API_TIMEOUT_SECONDS)  # type: ignore[return-value]  # sgs.get returns DataFrame for dict input


def get_selic(
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
    """Consulta a taxa Selic meta e efetiva do Banco Central do Brasil.

    Retorna os valores da Selic meta (série 432) e Selic efetiva/over (série 11)
    para o período informado.

    Args:
        data_inicio: Data inicial no formato YYYY-MM-DD. Padrão: 30 dias atrás.
        data_fim: Data final no formato YYYY-MM-DD. Padrão: hoje.

    Returns:
        JSON com os valores da Selic meta e efetiva no período.
    """
    logger.info("get_selic chamado: data_inicio=%s, data_fim=%s", data_inicio, data_fim)

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
        dt_inicio = dt_fim - timedelta(days=30)

    range_err = validate_date_range(dt_inicio, dt_fim, _MAX_DAYS)
    if range_err:
        return range_err

    try:
        df: pd.DataFrame = _fetch_selic(dt_inicio, dt_fim)

        if df.empty:
            return json.dumps(
                {"erro": "Nenhum dado da Selic encontrado no período informado."},
                ensure_ascii=False,
            )

        # O índice é a data
        df.index.name = "data"
        df = df.reset_index()
        df["data"] = df["data"].dt.strftime("%Y-%m-%d")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"periodo": {"inicio": str(dt_inicio), "fim": str(dt_fim)}, "selic": registros},
            ensure_ascii=False,
        )

    except FuturesTimeoutError:
        return erro_json("Tempo limite excedido ao consultar a API Selic do BCB. Tente novamente.")
    except requests.ConnectionError:
        return erro_json("Não foi possível conectar à API do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar Selic")
        return erro_json("Erro inesperado ao consultar Selic. Verifique os parâmetros.")
