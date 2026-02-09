"""Tool para consulta de cotações PTAX (câmbio) do Banco Central."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
from bcb import PTAX


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
    hoje = date.today()
    dt_fim = date.fromisoformat(data_fim) if data_fim else hoje
    dt_inicio = date.fromisoformat(data_inicio) if data_inicio else dt_fim - timedelta(days=30)

    try:
        ptax = PTAX()
        ep = ptax.get_endpoint("CotacaoMoedaPeriodo")

        df: pd.DataFrame = (
            ep.query()
            .parameters(
                moeda=moeda,
                dataInicial=dt_inicio.strftime("%m-%d-%Y"),
                dataFinalCotacao=dt_fim.strftime("%m-%d-%Y"),
            )
            .collect()
        )

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
        df = df[list(colunas_existentes.keys())].rename(columns=colunas_existentes)

        # Converter datetime para string ISO
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"moeda": moeda, "periodo": {"inicio": str(dt_inicio), "fim": str(dt_fim)}, "cotacoes": registros},
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"erro": f"Erro ao consultar PTAX: {e}"}, ensure_ascii=False)
