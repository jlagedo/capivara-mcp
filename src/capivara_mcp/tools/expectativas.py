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

# Subconjunto de indicadores de inflação (para endpoint 12 meses)
_INDICADORES_INFLACAO = {
    "IPCA",
    "IGP-M",
    "INPC",
    "IGP-DI",
    "IPCA Administrados",
    "IPCA Livres",
    "IPCA Serviços",
    "IPCA Alimentação no domicílio",
    "IPCA Bens industrializados",
}

# Renomeação padrão de colunas
_COLUNAS_BASE = {
    "Indicador": "indicador",
    "Data": "data_pesquisa",
    "DataReferencia": "periodo_referencia",
    "Media": "media",
    "Mediana": "mediana",
    "Minimo": "minimo",
    "Maximo": "maximo",
}


def _convert_datetime_columns(df: pd.DataFrame) -> None:
    """Converte colunas datetime para string ISO in-place."""
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Expectativas anuais (existente)
# ---------------------------------------------------------------------------

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

        df = df.rename(columns=_COLUNAS_BASE)
        _convert_datetime_columns(df)

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


# ---------------------------------------------------------------------------
# Expectativas mensais
# ---------------------------------------------------------------------------

def _fetch_expectativas_mensais(indicador: str, top: int) -> pd.DataFrame:
    """Busca expectativas mensais de mercado na API do BCB."""
    em = Expectativas()
    ep = em.get_endpoint("ExpectativaMercadoMensais")
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


def get_expectativas_mensais(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
    """Consulta expectativas mensais de mercado do Boletim Focus do Banco Central.

    Retorna as últimas expectativas mensais do mercado para o indicador escolhido,
    incluindo mediana, mínimo, máximo, data da pesquisa e período de referência mensal.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        indicador: Indicador econômico. Exemplos: "IPCA", "Selic", "PIB Total", "Câmbio".
            Padrão: "IPCA".
        top: Número de últimas expectativas a retornar. Padrão: 10.

    Returns:
        JSON com as expectativas mensais de mercado para o indicador.
    """
    logger.info("get_expectativas_mensais chamado: indicador=%s, top=%d", indicador, top)

    if indicador not in _INDICADORES:
        return erro_json(f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_INDICADORES))}.")

    try:
        df: pd.DataFrame = _fetch_expectativas_mensais(indicador, top)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhuma expectativa mensal encontrada para '{indicador}'."},
                ensure_ascii=False,
            )

        df = df.rename(columns=_COLUNAS_BASE)
        _convert_datetime_columns(df)

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"indicador": indicador, "frequencia": "mensal", "expectativas": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json(f"Tempo limite excedido ao consultar expectativas mensais de {indicador}. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Expectativas do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar expectativas mensais: indicador=%s", indicador)
        return erro_json(f"Erro inesperado ao consultar expectativas mensais de {indicador}. Verifique os parâmetros.")


# ---------------------------------------------------------------------------
# Expectativas Selic (por reunião COPOM)
# ---------------------------------------------------------------------------

def _fetch_expectativas_selic(top: int) -> pd.DataFrame:
    """Busca expectativas da Selic por reunião na API do BCB."""
    em = Expectativas()
    ep = em.get_endpoint("ExpectativasMercadoSelic")
    return (
        ep.query()
        .filter(ep.baseCalculo == 0)
        .orderby(ep.Data.desc())
        .select(
            ep.Data,
            ep.Reuniao,
            ep.Media,
            ep.Mediana,
            ep.Minimo,
            ep.Maximo,
        )
        .limit(top)
        .collect()
    )


def get_expectativas_selic(
    top: int = 10,
) -> str:
    """Consulta expectativas da Selic por reunião do COPOM do Banco Central.

    Retorna as últimas expectativas do mercado para a taxa Selic por reunião do COPOM,
    incluindo mediana, mínimo, máximo e data da reunião.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        top: Número de últimas expectativas a retornar. Padrão: 10.

    Returns:
        JSON com as expectativas da Selic por reunião.
    """
    logger.info("get_expectativas_selic chamado: top=%d", top)

    try:
        df: pd.DataFrame = _fetch_expectativas_selic(top)

        if df.empty:
            return json.dumps(
                {"erro": "Nenhuma expectativa da Selic encontrada."},
                ensure_ascii=False,
            )

        colunas = {
            "Data": "data_pesquisa",
            "Reuniao": "reuniao",
            "Media": "media",
            "Mediana": "mediana",
            "Minimo": "minimo",
            "Maximo": "maximo",
        }
        df = df.rename(columns=colunas)
        _convert_datetime_columns(df)

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"indicador": "Selic", "frequencia": "por_reuniao", "expectativas": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json("Tempo limite excedido ao consultar expectativas da Selic. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Expectativas do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar expectativas da Selic")
        return erro_json("Erro inesperado ao consultar expectativas da Selic. Verifique os parâmetros.")


# ---------------------------------------------------------------------------
# Expectativas de inflação 12 meses
# ---------------------------------------------------------------------------

def _fetch_expectativas_inflacao12m(indicador: str, top: int) -> pd.DataFrame:
    """Busca expectativas de inflação 12 meses na API do BCB."""
    em = Expectativas()
    ep = em.get_endpoint("ExpectativasMercadoInflacao12Meses")
    return (
        ep.query()
        .filter(ep.Indicador == indicador, ep.baseCalculo == 0)
        .orderby(ep.Data.desc())
        .select(
            ep.Indicador,
            ep.Data,
            ep.Media,
            ep.Mediana,
            ep.Minimo,
            ep.Maximo,
            ep.Suavizada,
        )
        .limit(top)
        .collect()
    )


def get_expectativas_inflacao12m(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
    """Consulta expectativas de inflação acumulada em 12 meses do Boletim Focus.

    Retorna as últimas expectativas do mercado para a inflação acumulada em 12 meses,
    incluindo mediana, mínimo, máximo e indicador de suavização.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        indicador: Indicador de inflação. Exemplos: "IPCA", "IGP-M", "INPC", "IGP-DI",
            "IPCA Administrados", "IPCA Livres", "IPCA Serviços". Padrão: "IPCA".
        top: Número de últimas expectativas a retornar. Padrão: 10.

    Returns:
        JSON com as expectativas de inflação 12 meses para o indicador.
    """
    logger.info("get_expectativas_inflacao12m chamado: indicador=%s, top=%d", indicador, top)

    if indicador not in _INDICADORES_INFLACAO:
        return erro_json(f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_INDICADORES_INFLACAO))}.")

    try:
        df: pd.DataFrame = _fetch_expectativas_inflacao12m(indicador, top)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhuma expectativa de inflação 12 meses encontrada para '{indicador}'."},
                ensure_ascii=False,
            )

        colunas = {
            "Indicador": "indicador",
            "Data": "data_pesquisa",
            "Media": "media",
            "Mediana": "mediana",
            "Minimo": "minimo",
            "Maximo": "maximo",
            "Suavizada": "suavizada",
        }
        df = df.rename(columns=colunas)
        _convert_datetime_columns(df)

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"indicador": indicador, "horizonte": "12_meses", "expectativas": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json(f"Tempo limite excedido ao consultar expectativas de inflação 12m de {indicador}. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Expectativas do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar expectativas inflação 12m: indicador=%s", indicador)
        return erro_json(f"Erro inesperado ao consultar expectativas de inflação 12m de {indicador}. Verifique os parâmetros.")


# ---------------------------------------------------------------------------
# Expectativas Top 5 anuais
# ---------------------------------------------------------------------------

def _fetch_expectativas_top5(indicador: str, top: int) -> pd.DataFrame:
    """Busca expectativas Top 5 anuais na API do BCB."""
    em = Expectativas()
    ep = em.get_endpoint("ExpectativasMercadoTop5Anuais")
    return (
        ep.query()
        .filter(ep.Indicador == indicador)
        .orderby(ep.Data.desc())
        .select(
            ep.Indicador,
            ep.Data,
            ep.DataReferencia,
            ep.tipoCalculo,
            ep.Media,
            ep.Mediana,
            ep.Minimo,
            ep.Maximo,
        )
        .limit(top)
        .collect()
    )


def get_expectativas_top5(
    indicador: str = "IPCA",
    top: int = 10,
) -> str:
    """Consulta expectativas Top 5 anuais do Boletim Focus do Banco Central.

    Retorna as últimas expectativas do Top 5 do mercado para o indicador escolhido,
    incluindo tipo de cálculo (curto/longo prazo), mediana, mínimo e máximo.
    Dados obtidos da API de Expectativas do BCB.

    Args:
        indicador: Indicador econômico. Exemplos: "IPCA", "Selic", "PIB Total", "Câmbio".
            Padrão: "IPCA".
        top: Número de últimas expectativas a retornar. Padrão: 10.

    Returns:
        JSON com as expectativas Top 5 para o indicador.
    """
    logger.info("get_expectativas_top5 chamado: indicador=%s, top=%d", indicador, top)

    if indicador not in _INDICADORES:
        return erro_json(f"Indicador '{indicador}' não suportado. Use: {', '.join(sorted(_INDICADORES))}.")

    try:
        df: pd.DataFrame = _fetch_expectativas_top5(indicador, top)

        if df.empty:
            return json.dumps(
                {"erro": f"Nenhuma expectativa Top 5 encontrada para '{indicador}'."},
                ensure_ascii=False,
            )

        colunas = {
            "Indicador": "indicador",
            "Data": "data_pesquisa",
            "DataReferencia": "periodo_referencia",
            "tipoCalculo": "tipo_calculo",
            "Media": "media",
            "Mediana": "mediana",
            "Minimo": "minimo",
            "Maximo": "maximo",
        }
        df = df.rename(columns=colunas)
        _convert_datetime_columns(df)

        registros = df.to_dict(orient="records")
        return json.dumps(
            {"indicador": indicador, "tipo": "top5_anual", "expectativas": registros},
            ensure_ascii=False,
        )

    except httpx.TimeoutException:
        return erro_json(f"Tempo limite excedido ao consultar expectativas Top 5 de {indicador}. Tente novamente.")
    except httpx.ConnectError:
        return erro_json("Não foi possível conectar à API de Expectativas do BCB. Verifique sua conexão.")
    except Exception:
        logger.exception("Erro ao consultar expectativas Top 5: indicador=%s", indicador)
        return erro_json(f"Erro inesperado ao consultar expectativas Top 5 de {indicador}. Verifique os parâmetros.")
