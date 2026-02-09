"""Tool para consulta de cotações PTAX (câmbio) do Banco Central."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

import httpx
import pandas as pd
from bcb import PTAX

from capivara_mcp.tools._validation import erro_json, parse_date, validate_date_range

logger = logging.getLogger("capivara-mcp.ptax")

_MAX_DAYS = 365


def _fetch_ptax(moeda: str, dt_inicio: date, dt_fim: date) -> pd.DataFrame:
    """Busca cotações PTAX na API do BCB."""
    ptax = PTAX()
    ep = ptax.get_endpoint("CotacaoMoedaPeriodo")
    return (
        ep.query()
        .parameters(
            moeda=moeda,
            dataInicial=dt_inicio.strftime("%m-%d-%Y"),
            dataFinalCotacao=dt_fim.strftime("%m-%d-%Y"),
        )
        .collect()
    )


def get_ptax(
    moeda: str = "USD",
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> str:
    """Consulta cotações PTAX (câmbio) do Banco Central do Brasil.

    Retorna cotações de compra e venda para a moeda informada no período.
    Os dados são obtidos da API oficial PTAX do BCB.

    Args:
        moeda: Código da moeda (ex: "USD", "EUR"). Padrão: "USD".
        data_inicio: Data inicial no formato YYYY-MM-DD. Padrão: 30 dias atrás.
        data_fim: Data final no formato YYYY-MM-DD. Padrão: hoje.

    Returns:
        JSON com as cotações de compra e venda no período.
    """
    logger.info("get_ptax chamado: moeda=%s, data_inicio=%s, data_fim=%s", moeda, data_inicio, data_fim)

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
        df: pd.DataFrame = _fetch_ptax(moeda, dt_inicio, dt_fim)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhuma cotação encontrada para {moeda} no período informado."},
                ensure_ascii=False,
            )

        # Selecionar e renomear colunas relevantes
        colunas = {
            "cotacaoCompra": "cotacao_compra",
            "cotacaoVenda": "cotacao_venda",
            "dataHoraCotacao": "data_hora",
            "tipoBoletim": "tipo_boletim",
        }
        colunas_existentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_existentes.keys())].rename(columns=colunas_existentes)  # type: ignore[call-overload]  # pandas rename typing

        # Converter datetime para string ISO
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"moeda": moeda, "periodo": {"inicio": str(dt_inicio), "fim": str(dt_fim)}, "cotacoes": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json("Tempo limite excedido ao consultar a API PTAX do BCB. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API PTAX do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar PTAX: moeda=%s", moeda)
        return erro_json(f"Erro inesperado ao consultar PTAX para {moeda}. Verifique os parâmetros.")
