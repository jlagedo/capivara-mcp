"""Tool para consulta de índices de inflação (IPCA e IGP-M) do Banco Central."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
from bcb import sgs


# Códigos das séries no SGS
_SERIES = {
    "IPCA": 433,
    "IGP-M": 189,
}


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
    indice_upper = indice.upper()
    if indice_upper not in _SERIES:
        return json.dumps(
            {"erro": f"Índice '{indice}' não suportado. Use 'IPCA' ou 'IGP-M'."},
            ensure_ascii=False,
        )

    hoje = date.today()
    dt_fim = date.fromisoformat(data_fim) if data_fim else hoje
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else dt_fim - timedelta(days=365)

    try:
        codigo = _SERIES[indice_upper]
        df: pd.DataFrame = sgs.get(
            {indice_upper: codigo},
            start=dt_inicio.strftime("%Y-%m-%d"),
            end=dt_fim.strftime("%Y-%m-%d"),
        )

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

    except Exception as e:
        return json.dumps({"erro": f"Erro ao consultar {indice_upper}: {e}"}, ensure_ascii=False)
