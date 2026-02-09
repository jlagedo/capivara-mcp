"""Tests for _validation.py — pure unit tests, no mocking needed."""

from __future__ import annotations

import json
from datetime import date

from capivara_mcp.tools._validation import erro_json, parse_date, validate_date_range


class TestErroJson:
    def test_returns_valid_json_with_erro_key(self):
        result = erro_json("something went wrong")
        data = json.loads(result)
        assert "erro" in data
        assert data["erro"] == "something went wrong"

    def test_preserves_portuguese_characters(self):
        result = erro_json("Data inválida para 'início'")
        data = json.loads(result)
        assert "inválida" in data["erro"]
        assert "início" in data["erro"]

    def test_returns_str_type(self):
        assert isinstance(erro_json("test"), str)


class TestParseDate:
    def test_valid_iso_date(self):
        result = parse_date("2025-01-15", "data_inicio")
        assert result == date(2025, 1, 15)

    def test_invalid_format_slash(self):
        result = parse_date("15/01/2025", "data_inicio")
        data = json.loads(result)
        assert "erro" in data
        assert "data_inicio" in data["erro"]

    def test_empty_string(self):
        result = parse_date("", "data_fim")
        data = json.loads(result)
        assert "erro" in data

    def test_nonsense_string(self):
        result = parse_date("not-a-date", "data_fim")
        data = json.loads(result)
        assert "erro" in data

    def test_error_message_includes_param_name(self):
        result = parse_date("bad", "meu_campo")
        data = json.loads(result)
        assert "meu_campo" in data["erro"]

    def test_error_message_includes_bad_value(self):
        result = parse_date("31-12-2025", "data_fim")
        data = json.loads(result)
        assert "31-12-2025" in data["erro"]


class TestValidateDateRange:
    def test_valid_range(self):
        result = validate_date_range(date(2025, 1, 1), date(2025, 1, 30), 365)
        assert result is None

    def test_same_day(self):
        result = validate_date_range(date(2025, 1, 1), date(2025, 1, 1), 365)
        assert result is None

    def test_start_after_end(self):
        result = validate_date_range(date(2025, 2, 1), date(2025, 1, 1), 365)
        data = json.loads(result)
        assert "erro" in data

    def test_exceeds_max_days(self):
        result = validate_date_range(date(2024, 1, 1), date(2025, 6, 1), 365)
        data = json.loads(result)
        assert "erro" in data
        assert "365" in data["erro"]

    def test_exactly_at_max_days(self):
        start = date(2025, 1, 1)
        end = date(2026, 1, 1)  # 365 days
        result = validate_date_range(start, end, 365)
        assert result is None

    def test_one_over_max_days(self):
        start = date(2025, 1, 1)
        end = date(2026, 1, 2)  # 366 days
        result = validate_date_range(start, end, 365)
        data = json.loads(result)
        assert "erro" in data
