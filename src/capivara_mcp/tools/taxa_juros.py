"""Tool para consulta de taxas de juros por instituição financeira do Banco Central."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import json
import logging
import re

import httpx
import pandas as pd
from bcb import TaxaJuros

from capivara_mcp.tools._validation import erro_json

logger = logging.getLogger("capivara-mcp.taxa_juros")

_MES_REGEX = re.compile(r"^[A-Z][a-z]{2}-\d{4}$")


def _fetch_taxa_juros(mes: str, modalidade: str | None, top: int) -> pd.DataFrame:
    """Busca taxas de juros por mês na API do BCB."""
    tj = TaxaJuros()
    ep = tj.get_endpoint("TaxasJurosMensalPorMes")
    query = ep.query().filter(ep.Mes == mes)
    if modalidade:
        query = query.filter(ep.Modalidade == modalidade)
    return query.orderby(ep.TaxaJurosAoAno.asc()).limit(top).collect()


def get_taxa_juros(
    mes: str,
    modalidade: str | None = None,
    top: int = 20,
) -> str:
    """Consulta taxas de juros por instituição financeira do Banco Central.

    Retorna as taxas de juros mensais e anuais praticadas por instituições financeiras
    para o mês informado, opcionalmente filtradas por modalidade de crédito.
    Dados obtidos da API de Taxas de Juros do BCB.

    Args:
        mes: Mês de referência no formato "MMM-YYYY" (ex: "Jan-2025", "Fev-2025").
        modalidade: Filtro opcional por modalidade de crédito (ex: "CHEQUE ESPECIAL").
        top: Número máximo de resultados. Padrão: 20.

    Returns:
        JSON com as taxas de juros por instituição para o mês.
    """
    logger.info("get_taxa_juros chamado: mes=%s, modalidade=%s, top=%d", mes, modalidade, top)

    if not _MES_REGEX.match(mes):
        return erro_json(f"Formato de mês inválido: '{mes}'. Use o formato 'MMM-YYYY' (ex: 'Jan-2025').")

    try:
        df: pd.DataFrame = _fetch_taxa_juros(mes, modalidade, top)

        if df.empty:
            msg = f"Nenhuma taxa de juros encontrada para {mes}"
            if modalidade:
                msg += f" na modalidade '{modalidade}'"
            msg += "."
            return json.dumps({"erro": msg}, ensure_ascii=False)

        colunas = {
            "InstituicaoFinanceira": "instituicao",
            "Modalidade": "modalidade",
            "TaxaJurosAoMes": "taxa_mensal",
            "TaxaJurosAoAno": "taxa_anual",
            "cnpj8": "cnpj8",
        }
        colunas_existentes = {k: v for k, v in colunas.items() if k in df.columns}
        df = df[list(colunas_existentes.keys())].rename(columns=colunas_existentes)

        # Converter datetime para string ISO
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"mes": mes, "taxas": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json(f"Tempo limite excedido ao consultar taxas de juros para {mes}. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Taxas de Juros do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar taxas de juros: mes=%s", mes)
        return erro_json(f"Erro inesperado ao consultar taxas de juros para {mes}. Verifique os parâmetros.")
