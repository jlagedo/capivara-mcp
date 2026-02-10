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


def make_expectativas_mensais_df(indicador: str = "IPCA", n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching ExpectativaMercadoMensais response shape.

    DataReferencia is a string "MM/YYYY" (monthly reference).
    """
    rows = []
    base = datetime(2025, 1, 10)
    for i in range(n):
        rows.append(
            {
                "Indicador": indicador,
                "Data": base - pd.Timedelta(days=i * 7),
                "DataReferencia": f"{(i % 12) + 1:02d}/2025",
                "Media": 0.45 + i * 0.01,
                "Mediana": 0.44 + i * 0.01,
                "Minimo": 0.30,
                "Maximo": 0.60,
            }
        )
    df = pd.DataFrame(rows)
    df["Data"] = pd.to_datetime(df["Data"])
    return df


def make_expectativas_selic_df(n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching ExpectativasMercadoSelic response shape.

    Has Reuniao field, no Indicador field.
    """
    rows = []
    base = datetime(2025, 1, 10)
    for i in range(n):
        rows.append(
            {
                "Data": base - pd.Timedelta(days=i * 7),
                "Reuniao": f"R{45 + i}/2025",
                "Media": 14.75 + i * 0.25,
                "Mediana": 14.75 + i * 0.25,
                "Minimo": 14.25,
                "Maximo": 15.25,
            }
        )
    df = pd.DataFrame(rows)
    df["Data"] = pd.to_datetime(df["Data"])
    return df


def make_expectativas_inflacao12m_df(indicador: str = "IPCA", n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching ExpectativasMercadoInflacao12Meses response shape.

    Includes extra Suavizada field.
    """
    rows = []
    base = datetime(2025, 1, 10)
    for i in range(n):
        rows.append(
            {
                "Indicador": indicador,
                "Data": base - pd.Timedelta(days=i * 7),
                "Media": 4.50 + i * 0.1,
                "Mediana": 4.48 + i * 0.1,
                "Minimo": 3.80,
                "Maximo": 5.20,
                "Suavizada": "S" if i % 2 == 0 else "N",
            }
        )
    df = pd.DataFrame(rows)
    df["Data"] = pd.to_datetime(df["Data"])
    return df


def make_expectativas_top5_df(indicador: str = "IPCA", n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching ExpectativasMercadoTop5Anuais response shape.

    Includes tipoCalculo field and DataReferencia as year.
    """
    rows = []
    base = datetime(2025, 1, 10)
    for i in range(n):
        rows.append(
            {
                "Indicador": indicador,
                "Data": base - pd.Timedelta(days=i * 7),
                "DataReferencia": 2025,
                "tipoCalculo": "C" if i % 2 == 0 else "L",
                "Media": 4.50 + i * 0.1,
                "Mediana": 4.48 + i * 0.1,
                "Minimo": 3.80,
                "Maximo": 5.20,
            }
        )
    df = pd.DataFrame(rows)
    df["Data"] = pd.to_datetime(df["Data"])
    return df


def make_taxa_juros_df(n: int = 3) -> pd.DataFrame:
    """Build a DataFrame matching TaxasJurosMensalPorMes response shape."""
    rows = []
    instituicoes = ["CAIXA ECONOMICA FEDERAL", "BANCO DO BRASIL", "ITAU UNIBANCO"]
    for i in range(n):
        rows.append(
            {
                "InstituicaoFinanceira": instituicoes[i % len(instituicoes)],
                "Modalidade": "FINANCIAMENTO IMOBILIARIO",
                "TaxaJurosAoMes": 0.39 + i * 0.05,
                "TaxaJurosAoAno": 4.75 + i * 0.5,
                "cnpj8": f"0036030{i}",
            }
        )
    return pd.DataFrame(rows)
