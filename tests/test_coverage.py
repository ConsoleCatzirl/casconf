"""Tests targeting coverage gaps in merger, discovery, parser,
registry, cli, and the public __init__ API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# cascconf/__init__.py  (merge_configs / validate_config)
# ---------------------------------------------------------------------------


class TestMergeConfigsPublicApi:
    """Covers cascconf/__init__.py lines 86-105."""

    def test_returns_dict_when_no_output(self, tmp_path):
        """merge_configs() returns dict when output=None."""
        import yaml
        from cascconf import merge_configs

        dc = tmp_path / "cascconf.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [str(FIXTURES / "base")],
                    "patterns": ["config.json"],
                }
            ),
            encoding="utf-8",
        )
        result = merge_configs(discovery_config=str(dc))
        assert isinstance(result, dict)
        assert "database" in result

    def test_writes_file_and_returns_none(self, tmp_path):
        """merge_configs() returns None when output is given."""
        import yaml
        from cascconf import merge_configs

        dc = tmp_path / "cascconf.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [str(FIXTURES / "base")],
                    "patterns": ["config.json"],
                }
            ),
            encoding="utf-8",
        )
        out = tmp_path / "merged.json"
        result = merge_configs(
            discovery_config=str(dc), output=str(out)
        )
        assert result is None
        assert out.exists()

    def test_uses_env_var_when_discovery_config_is_none(
        self, tmp_path, monkeypatch
    ):
        """merge_configs(None) uses CASCCONF_DISCOVERY env var."""
        import yaml
        from cascconf import merge_configs

        dc = tmp_path / "env.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [str(FIXTURES / "base")],
                    "patterns": ["config.json"],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("CASCCONF_DISCOVERY", str(dc))
        result = merge_configs(discovery_config=None)
        assert isinstance(result, dict)

    def test_validate_config_passes_valid_schema(self):
        """validate_config() does not raise for a conforming dict."""
        from cascconf import validate_config

        schema = {
            "type": "object",
            "properties": {"host": {"type": "string"}},
        }
        validate_config({"host": "localhost"}, schema=schema)

    def test_validate_config_raises_on_invalid(self):
        """validate_config() raises CascConfValidationError."""
        from cascconf import validate_config
        from cascconf.exceptions import CascConfValidationError

        schema = {
            "type": "object",
            "required": ["host"],
            "properties": {"host": {"type": "string"}},
        }
        with pytest.raises(CascConfValidationError) as exc_info:
            validate_config({}, schema=schema)
        assert exc_info.value.errors

    def test_validate_config_loads_schema_from_file(self, tmp_path):
        """validate_config() accepts a path to a JSON schema file."""
        from cascconf import validate_config

        schema_file = tmp_path / "schema.json"
        schema_file.write_text(
            json.dumps({"type": "object"}), encoding="utf-8"
        )
        validate_config({"a": 1}, schema=str(schema_file))


# ---------------------------------------------------------------------------
# cascconf/discovery.py  (from_file edge cases, __eq__, path-not-dir)
# ---------------------------------------------------------------------------


class TestDiscoveryConfigFromFile:
    """Covers discovery.py lines 109, 115-116."""

    def test_unsupported_extension_raises(self, tmp_path):
        from cascconf.discovery import DiscoveryConfig
        from cascconf.exceptions import CascConfConfigError

        p = tmp_path / "dc.xml"
        p.write_text("<config/>", encoding="utf-8")
        with pytest.raises(CascConfConfigError, match="Unsupported"):
            DiscoveryConfig.from_file(p)

    def test_bad_yaml_content_raises(self, tmp_path):
        from cascconf.discovery import DiscoveryConfig
        from cascconf.exceptions import CascConfConfigError

        p = tmp_path / "dc.yaml"
        # Valid YAML but missing required keys triggers CascConfConfigError
        # via from_dict, not the parser; use truly unparseable YAML
        p.write_text(
            "directories: [/tmp\npatterns: [\n",
            encoding="utf-8",
        )
        with pytest.raises(CascConfConfigError):
            DiscoveryConfig.from_file(p)


class TestDiscoveryConfigEquality:
    """Covers discovery.py lines 160-162 (__eq__ non-DiscoveryConfig)."""

    def test_eq_with_non_discovery_config_returns_not_implemented(self):
        from cascconf.discovery import DiscoveryConfig

        dc = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        result = dc.__eq__("not a DiscoveryConfig")
        assert result is NotImplemented

    def test_eq_same_values_returns_true(self):
        from cascconf.discovery import DiscoveryConfig

        dc1 = DiscoveryConfig(
            directories=["/tmp"], patterns=["*.json"]
        )
        dc2 = DiscoveryConfig(
            directories=["/tmp"], patterns=["*.json"]
        )
        assert dc1 == dc2

    def test_eq_different_strategy_returns_false(self):
        from cascconf.discovery import DiscoveryConfig

        dc1 = DiscoveryConfig(
            directories=["/tmp"],
            patterns=["*.json"],
            merge_strategy="deep",
        )
        dc2 = DiscoveryConfig(
            directories=["/tmp"],
            patterns=["*.json"],
            merge_strategy="shallow",
        )
        assert dc1 != dc2


class TestDiscoverPathNotDir:
    """Covers discovery.py lines 207-211 (path is not a directory)."""

    def test_file_path_used_as_directory_is_skipped(self, tmp_path):
        from cascconf.discovery import DiscoveryConfig, discover

        # Use a regular file as a directory — should be warned and skipped
        f = tmp_path / "not_a_dir.json"
        f.write_text("{}", encoding="utf-8")
        dc = DiscoveryConfig(
            directories=[str(f)], patterns=["*.json"]
        )
        found = discover(dc)
        assert found == []


# ---------------------------------------------------------------------------
# cascconf/merger.py  (type conflict warning — line 85)
# ---------------------------------------------------------------------------


class TestDeepMergeTypeConflict:
    """Covers merger.py line 85 (logger.warning on type conflict)."""

    def test_type_conflict_override_wins(self):
        from cascconf.merger import deep_merge

        base = {"key": "a string"}
        override = {"key": {"nested": "dict"}}
        result = deep_merge(base, override)
        assert result["key"] == {"nested": "dict"}

    def test_type_conflict_logs_warning(self, caplog):
        import logging

        from cascconf.merger import deep_merge

        with caplog.at_level(logging.WARNING, logger="cascconf.merger"):
            deep_merge({"key": "string"}, {"key": 42})
        assert any("conflict" in r.message.lower() for r in caplog.records)


# ---------------------------------------------------------------------------
# cascconf/parser.py  (all-parsers-fail — line 77)
# ---------------------------------------------------------------------------


class TestParserFallbackAllFail:
    """Covers parser.py line 77 (CascConfParseError after all fail)."""

    def test_truly_unparseable_file_raises(self, tmp_path):
        from cascconf.exceptions import CascConfParseError
        from cascconf.parser import parse

        f = tmp_path / "garbage.unknown"
        f.write_bytes(b"\xff\xfe\xfd")  # invalid for all text parsers
        with pytest.raises(CascConfParseError):
            parse(f)


# ---------------------------------------------------------------------------
# cascconf/registry.py  (TOML writer — lines 182-186)
# ---------------------------------------------------------------------------


class TestRegistryTomlWriter:
    """Covers registry.py lines 182-186 (_write_toml)."""

    def test_toml_output_is_written(self, tmp_path):
        from cascconf.writer import write

        dest = tmp_path / "out.toml"
        write({"name": "cascconf", "version": "1.0"}, output=dest, fmt="toml")
        assert dest.exists()
        content = dest.read_text(encoding="utf-8")
        assert "cascconf" in content


class TestRegistryTomlParser:
    """Covers registry.py lines 136-141 (_parse_toml)."""

    def test_parses_toml_file(self, tmp_path):
        from cascconf.parser import parse

        f = tmp_path / "config.toml"
        f.write_text(
            '[database]\nhost = "localhost"\nport = 5432\n',
            encoding="utf-8",
        )
        result = parse(f)
        assert result["database"]["host"] == "localhost"


# ---------------------------------------------------------------------------
# cascconf/cli.py  (verbose logging, unexpected exception — 119, 204-209)
# ---------------------------------------------------------------------------


class TestCliConfigureLogging:
    """Covers cli.py line 119 (verbose branch)."""

    def test_verbose_calls_basicconfig_with_debug(self, monkeypatch):
        import logging

        from cascconf.cli import _configure_logging

        captured: list[int] = []

        def fake_basicconfig(**kwargs: object) -> None:
            captured.append(kwargs.get("level"))  # type: ignore[arg-type]

        monkeypatch.setattr(logging, "basicConfig", fake_basicconfig)
        _configure_logging(verbose=True)
        assert captured == [logging.DEBUG]


class TestCliUnexpectedException:
    """Covers cli.py lines 204-209 (bare except branch)."""

    def test_unexpected_exception_returns_1(
        self, tmp_path, monkeypatch
    ):
        import yaml

        from cascconf import cli

        dc = tmp_path / "cascconf.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [str(FIXTURES / "base")],
                    "patterns": ["config.json"],
                }
            ),
            encoding="utf-8",
        )

        # Patch write to raise an unexpected (non-CascConf) exception
        # Must patch the name as imported in cascconf.cli
        import cascconf.cli as cli_module

        monkeypatch.setattr(
            cli_module,
            "write",
            lambda *a, **kw: (_ for _ in ()).throw(
                RuntimeError("unexpected")
            ),
        )

        rc = cli.main(["--discovery-config", str(dc)])
        assert rc == 1


class TestCliRunWithDiscoveryConfigObject:
    """Covers cli.py lines 159→164 (DiscoveryConfig branch in run())."""

    def test_run_accepts_discovery_config_object(self):
        from cascconf.cli import run
        from cascconf.discovery import DiscoveryConfig

        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        result = run(discovery_config=dc)
        assert isinstance(result, dict)
        assert "database" in result
