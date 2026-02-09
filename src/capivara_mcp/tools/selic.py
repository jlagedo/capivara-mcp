"""Tool para consulta da taxa Selic (meta e efetiva) do Banco Central."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
from bcb import sgs


# Códigos das séries no SGS
_SERIES = {
    "meta": 432,
    "efetiva": 11,
}


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
    hoje = date.today()
    dt_fim = date.fromisoformat(data_fim) if data_fim else hoje
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else dt_fim - timedelta(days=30)

    try:
        df: pd.DataFrame = sgs.get(
            {"selic_meta": _SERIES["meta"], "selic_efetiva": _SERIES["efetiva"]},
            start=dt_inicio.strftime("%Y-%m-%d"),
            end=dt_fim.strftime("%Y-%m-%d"),
        )

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

    except Exception as e:
        return json.dumps({"erro": f"Erro ao consultar Selic: {e}"}, ensure_ascii=False)
