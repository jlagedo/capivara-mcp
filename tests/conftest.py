"""Shared fixtures and DataFrame factories for capivara-mcp tests."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


def make_ptax_df(n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching PTAX CotacaoMoedaPeriodo response shape."""
    rows = []
    base = datetime(2025, 1, 2, 13, 0, 0)
    for i in range(n):
        rows.append(
            {
                "cotacaoCompra": 5.10 + i * 0.01,
                "cotacaoVenda": 5.12 + i * 0.01,
                "dataHoraCotacao": base + pd.Timedelta(days=i),
                "tipoBoletim": "Fechamento",
            }
        )
    df = pd.DataFrame(rows)
    df["dataHoraCotacao"] = pd.to_datetime(df["dataHoraCotacao"])
    return df


def make_sgs_df(columns: dict[str, float], n: int = 5) -> pd.DataFrame:
    """Build a DataFrame matching SGS multi-series response (sgs.get with dict codes).

    Args:
        columns: Mapping of column name to base value (e.g. {"selic_meta": 10.5}).
        n: Number of rows.
    """
    dates = pd.date_range(start="2025-01-02", periods=n, freq="B")
    data = {name: [base + i * 0.01 for i in range(n)] for name, base in columns.items()}
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    return df


def make_expectativas_df(indicador: str = "Selic", n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching Expectativas ExpectativasMercadoAnuais response shape."""
    rows = []
    base = datetime(2025, 1, 10)
    for i in range(n):
        rows.append(
            {
                "Indicador": indicador,
                "Data": base - pd.Timedelta(days=i * 7),
                "DataReferencia": 2025,
                "Media": 13.5 + i * 0.1,
                "Mediana": 13.5 + i * 0.1,
                "Minimo": 12.0,
                "Maximo": 15.0,
            }
        )
    df = pd.DataFrame(rows)
    df["Data"] = pd.to_datetime(df["Data"])
    return df
