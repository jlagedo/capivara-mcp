"""Tool para consulta de expectativas de mercado (Focus) do Banco Central."""

from __future__ import annotations

import json

import pandas as pd
from bcb import Expectativas


# Mapeamento de indicadores aceitos
_INDICADORES = {"Selic", "IPCA", "PIB", "Câmbio"}


def get_expectativas_mercado(
    indicador: str = "Selic",
    top: int = 5,
) -> str:
    """Consulta expectativas de mercado do Boletim Focus do Banco Central.

    Retorna as últimas expectativas anuais do mercado para o indicador escolhido,
    incluindo mediana, mínimo, máximo, data da pesquisa e período de referência.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        indicador: Indicador econômico: "Selic", "IPCA", "PIB" ou "Câmbio". Padrão: "Selic".
        top: Número de últimas expectativas a retornar. Padrão: 5.

    Returns:
        JSON com as expectativas de mercado para o indicador.
    """
    if indicador not in _INDICADORES:
        return json.dumps(
            {"erro": f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_INDICADORES))}."},
            ensure_ascii=False,
        )

    try:
        em = Expectativas()
        ep = em.get_endpoint("ExpectativasMercadoAnuais")

        df: pd.DataFrame = (
            ep.query()
            .filter(ep.Indicador == indicador, ep.baseCalculo == 0)
            .orderby(ep.Data.desc())
            .select(
                ep.Indicador,
                ep.Data,
                ep.DataReferencia,
                ep.Media,
                ep.Mediana,
                ep.Minimo,
                ep.Maximo,
            )
            .limit(top)
            .collect()
        )

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhuma expectativa encontrada para '{indicador}'."},
                ensure_ascii=False,
            )

        # Renomear colunas para snake_case em português
        colunas = {
            "Indicador": "indicador",
            "Data": "data_pesquisa",
            "DataReferencia": "periodo_referencia",
            "Media": "media",
            "Mediana": "mediana",
            "Minimo": "minimo",
            "Maximo": "maximo",
        }
        df = df.rename(columns=colunas)

        # Converter datetime para string ISO
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d")

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"indicador": indicador, "expectativas": registros},
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"erro": f"Erro ao consultar expectativas de {indicador}: {e}"},
            ensure_ascii=False,
        )
