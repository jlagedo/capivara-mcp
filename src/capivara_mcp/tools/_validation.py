"""Utilitários compartilhados de validação para os tools do capivara-mcp."""

from __future__ import annotations

import json
from datetime import date


def erro_json(msg: str) -> str:
    """Retorna JSON com chave 'erro' para respostas de erro padronizadas."""
    return json.dumps({"erro": msg}, ensure_ascii=False)


def parse_date(value: str, param_name: str) -> date | str:
    """Converte string ISO para date, retornando erro JSON se inválida.

    Returns:
        date se válido, ou string JSON de erro se inválido.
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        return erro_json(f"Data inválida para '{param_name}': '{value}'. Use o formato YYYY-MM-DD.")


def validate_date_range(dt_inicio: date, dt_fim: date, max_days: int) -> str | None:
    """Valida que o intervalo de datas é coerente e dentro do limite.

    Returns:
        None se válido, ou string JSON de erro se inválido.
    """
    if dt_inicio > dt_fim:
        return erro_json(f"data_inicio ({dt_inicio}) não pode ser posterior a data_fim ({dt_fim}).")
    dias = (dt_fim - dt_inicio).days
    if dias > max_days:
        return erro_json(f"Intervalo de {dias} dias excede o limite de {max_days} dias. Reduza o período consultado.")
    return None
