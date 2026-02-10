"""Tool para consulta de indicadores de atividade econômica do Banco Central."""

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

logger = logging.getLogger("capivara-mcp.atividade")

_MAX_DAYS = 1825  # ~5 anos (dados mensais)
_API_TIMEOUT_SECONDS = 30


# Códigos das séries no SGS
_SERIES = {
    "PIB mensal": 4380,
    "Dívida bruta/PIB": 4513,
    "Resultado primário": 5793,
}


def _fetch_atividade(indicador: str, codigo: int, dt_inicio: date, dt_fim: date) -> pd.DataFrame:
    """Busca indicador de atividade econômica na API SGS do BCB."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            sgs.get,
            {indicador: codigo},
            start=dt_inicio.strftime("%Y-%m-%d"),
            end=dt_fim.strftime("%Y-%m-%d"),
        )
        return future.result(timeout=_API_TIMEOUT_SECONDS)  # type: ignore[return-value]


def get_atividade_economica(
    indicador: str = "PIB mensal",
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
    """Consulta indicadores de atividade econômica do Banco Central do Brasil.

    Retorna os valores mensais do indicador escolhido para o período.
    Dados obtidos do SGS (Sistema Gerenciador de Séries Temporais) do BCB.

    Args:
        indicador: Indicador desejado: "PIB mensal", "Dívida bruta/PIB" ou "Resultado primário".
            Padrão: "PIB mensal".
        data_inicio: Data inicial no formato YYYY-MM-DD. Padrão: 365 dias atrás.
        data_fim: Data final no formato YYYY-MM-DD. Padrão: hoje.

    Returns:
        JSON com os valores mensais do indicador no período.
    """
    logger.info("get_atividade_economica chamado: indicador=%s, data_inicio=%s, data_fim=%s", indicador, data_inicio, data_fim)

    if indicador not in _SERIES:
        return json.dumps(
            {"erro": f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_SERIES))}."},
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
        codigo = _SERIES[indicador]
        df: pd.DataFrame = _fetch_atividade(indicador, codigo, dt_inicio, dt_fim)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhum dado de {indicador} encontrado no período informado."},
                ensure_ascii=False,
            )

        df.index.name = "data"
        df = df.reset_index()
        df["data"] = df["data"].dt.strftime("%Y-%m-%d")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {
                "indicador": indicador,
                "periodo": {"inicio": str(dt_inicio), "fim": str(dt_fim)},
                "valores": registros,
            },
            ensure_ascii=False,
        )

    except FuturesTimeoutError:
        return erro_json(f"Tempo limite excedido ao consultar {indicador} na API do BCB. Tente novamente.")
    except requests.ConnectionError:
        return erro_json("Não foi possível conectar à API do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar atividade econômica: indicador=%s", indicador)
        return erro_json(f"Erro inesperado ao consultar {indicador}. Verifique os parâmetros.")
