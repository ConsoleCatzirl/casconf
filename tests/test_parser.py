"""Tests for casconf.parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from casconf.exceptions import CasConfParseError
from casconf.parser import parse

# Path to the test fixtures directory
FIXTURES = Path(__file__).parent / "fixtures"


class TestParseJson:
    """parse() with JSON files."""

    def test_parses_valid_json(self):
        result = parse(FIXTURES / "base" / "config.json")
        assert isinstance(result, dict)
        assert "database" in result

    def test_json_values_correct(self):
        result = parse(FIXTURES / "base" / "config.json")
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432

    def test_empty_json_file_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("", encoding="utf-8")
        assert parse(f) == {}

    def test_invalid_json_raises_parse_error(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(CasConfParseError) as exc_info:
            parse(f)
        assert exc_info.value.path == f

    def test_parse_error_contains_file_path(self, tmp_path):
        f = tmp_path / "broken.json"
        f.write_text("[not a dict]", encoding="utf-8")
        # A JSON list is not a valid config dict at top level
        # (parser returns it; this tests that the path is set)
        # Actually parse returns the list as-is; test bad syntax
        f.write_text("{bad:", encoding="utf-8")
        with pytest.raises(CasConfParseError) as exc_info:
            parse(f)
        assert exc_info.value.path == f


class TestParseYaml:
    """parse() with YAML files."""

    def test_parses_valid_yaml(self):
        result = parse(FIXTURES / "override" / "config.yaml")
        assert isinstance(result, dict)
        assert "database" in result

    def test_yaml_values_correct(self):
        result = parse(FIXTURES / "override" / "config.yaml")
        assert result["database"]["port"] == 5433

    def test_empty_yaml_file_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        assert parse(f) == {}


class TestParseIni:
    """parse() with INI files."""

    def test_parses_valid_ini(self):
        result = parse(FIXTURES / "extra" / "config.ini")
        assert isinstance(result, dict)
        assert "database" in result

    def test_ini_section_values_correct(self):
        result = parse(FIXTURES / "extra" / "config.ini")
        assert result["database"]["name"] == "myapp_dev"


class TestParseErrors:
    """parse() error handling."""

    def test_missing_file_raises_parse_error(self, tmp_path):
        f = tmp_path / "nonexistent.json"
        with pytest.raises(CasConfParseError) as exc_info:
            parse(f)
        assert exc_info.value.path == f

    def test_unknown_extension_tries_fallback(self, tmp_path):
        # A valid JSON file with an unknown extension should parse
        f = tmp_path / "config.unknown"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = parse(f)
        assert result == {"key": "value"}
