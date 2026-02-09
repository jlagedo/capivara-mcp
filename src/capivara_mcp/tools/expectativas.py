"""Tool para consulta de expectativas de mercado (Focus) do Banco Central."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import json
import logging

import httpx
import pandas as pd
from bcb import Expectativas

from capivara_mcp.tools._validation import erro_json

logger = logging.getLogger("capivara-mcp.expectativas")


# Mapeamento de indicadores aceitos
_INDICADORES = {
    "Balança comercial",
    "Câmbio",
    "Conta corrente",
    "Dívida bruta do governo geral",
    "Dívida líquida do setor público",
    "IGP-M",
    "Investimento direto no país",
    "IPCA",
    "IPCA Administrados",
    "IPCA Alimentação no domicílio",
    "IPCA Bens industrializados",
    "IPCA Livres",
    "IPCA Serviços",
    "PIB Agropecuária",
    "PIB Despesa de consumo da administração pública",
    "PIB Despesa de consumo das famílias",
    "PIB Exportação de bens e serviços",
    "PIB Formação Bruta de Capital Fixo",
    "PIB Importação de bens e serviços",
    "PIB Indústria",
    "PIB Serviços",
    "PIB Total",
    "Resultado nominal",
    "Resultado primário",
    "Selic",
    "Taxa de desocupação",
}


def _fetch_expectativas(indicador: str, top: int) -> pd.DataFrame:
    """Busca expectativas de mercado na API do BCB."""
    em = Expectativas()
    ep = em.get_endpoint("ExpectativasMercadoAnuais")
    return (
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


def get_expectativas_mercado(
    indicador: str = "Selic",
    top: int = 5,
) -> str:
    """Consulta expectativas de mercado do Boletim Focus do Banco Central.

    Retorna as últimas expectativas anuais do mercado para o indicador escolhido,
    incluindo mediana, mínimo, máximo, data da pesquisa e período de referência.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        indicador: Indicador econômico. Exemplos: "Selic", "IPCA", "PIB Total", "Câmbio",
            "IGP-M", "Taxa de desocupação", "Balança comercial", entre outros. Padrão: "Selic".
        top: Número de últimas expectativas a retornar. Padrão: 5.

    Returns:
        JSON com as expectativas de mercado para o indicador.
    """
    logger.info("get_expectativas_mercado chamado: indicador=%s, top=%d", indicador, top)

    if indicador not in _INDICADORES:
        return erro_json(f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_INDICADORES))}.")

    try:
        df: pd.DataFrame = _fetch_expectativas(indicador, top)

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

    except httpx.TimeoutException:
        return erro_json(f"Tempo limite excedido ao consultar expectativas de {indicador}. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Expectativas do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar expectativas: indicador=%s", indicador)
        return erro_json(f"Erro inesperado ao consultar expectativas de {indicador}. Verifique os parâmetros.")
