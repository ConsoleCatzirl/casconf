"""Tests targeting coverage gaps in merger, discovery, parser,
registry, cli, and the public API."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# casconf/api.py  (merge_configs)
# ---------------------------------------------------------------------------


class TestMergeConfigsPublicApi:
    """Covers casconf/api.py merge_configs."""

    def test_returns_dict_when_no_output(self, tmp_path):
        """merge_configs() returns dict when output=None."""
        import yaml

        from casconf import merge_configs

        dc = tmp_path / "casconf.yaml"
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

        from casconf import merge_configs

        dc = tmp_path / "casconf.yaml"
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
        result = merge_configs(discovery_config=str(dc), output=str(out))
        assert result is None
        assert out.exists()

    def test_uses_env_var_when_discovery_config_is_none(self, tmp_path, monkeypatch):
        """merge_configs(None) uses CASCCONF_DISCOVERY env var."""
        import yaml

        from casconf import merge_configs

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


# ---------------------------------------------------------------------------
# casconf/discovery.py  (from_file edge cases, __eq__, path-not-dir)
# ---------------------------------------------------------------------------


class TestDiscoveryConfigFromFile:
    """Covers discovery.py lines 109, 115-116."""

    def test_unsupported_extension_raises(self, tmp_path):
        from casconf.discovery import DiscoveryConfig
        from casconf.exceptions import CasConfConfigError

        p = tmp_path / "dc.xml"
        p.write_text("<config/>", encoding="utf-8")
        with pytest.raises(CasConfConfigError, match="Unsupported"):
            DiscoveryConfig.from_file(p)

    def test_bad_yaml_content_raises(self, tmp_path):
        from casconf.discovery import DiscoveryConfig
        from casconf.exceptions import CasConfConfigError

        p = tmp_path / "dc.yaml"
        # Valid YAML but missing required keys triggers CasConfConfigError
        # via from_dict, not the parser; use truly unparseable YAML
        p.write_text(
            "directories: ['/tmp']\npatterns: [\n",
            encoding="utf-8",
        )
        with pytest.raises(CasConfConfigError):
            DiscoveryConfig.from_file(p)


class TestDiscoveryConfigEquality:
    """Covers discovery.py lines 160-162 (__eq__ non-DiscoveryConfig)."""

    def test_eq_with_non_discovery_config_returns_not_implemented(self):
        from casconf.discovery import DiscoveryConfig

        dc = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        result = dc.__eq__("not a DiscoveryConfig")
        assert result is NotImplemented

    def test_eq_same_values_returns_true(self):
        from casconf.discovery import DiscoveryConfig

        dc1 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        dc2 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        assert dc1 == dc2

    def test_eq_different_strategy_returns_false(self):
        from casconf.discovery import DiscoveryConfig

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
        from casconf.discovery import DiscoveryConfig, discover

        # Use a regular file as a directory — should be warned and skipped
        f = tmp_path / "not_a_dir.json"
        f.write_text("{}", encoding="utf-8")
        dc = DiscoveryConfig(directories=[str(f)], patterns=["*.json"])
        found = discover(dc)
        assert found == []


# ---------------------------------------------------------------------------
# casconf.merger.py  (type conflict warning — line 85)
# ---------------------------------------------------------------------------


class TestDeepMergeTypeConflict:
    """Covers merger.py line 85 (logger.warning on type conflict)."""

    def test_type_conflict_override_wins(self):
        from casconf.merger import deep_merge

        base = {"key": "a string"}
        override = {"key": {"nested": "dict"}}
        result = deep_merge(base, override)
        assert result["key"] == {"nested": "dict"}

    def test_type_conflict_logs_warning(self, caplog):
        import logging

        from casconf.merger import deep_merge

        with caplog.at_level(logging.WARNING, logger="casconf.merger"):
            deep_merge({"key": "string"}, {"key": 42})
        assert any("conflict" in r.message.lower() for r in caplog.records)


# ---------------------------------------------------------------------------
# casconf/parser.py  (all-parsers-fail — line 77)
# ---------------------------------------------------------------------------


class TestParserFallbackAllFail:
    """Covers parser.py line 77 (CasConfParseError after all fail)."""

    def test_truly_unparseable_file_raises(self, tmp_path):
        from casconf.exceptions import CasConfParseError
        from casconf.parser import parse

        f = tmp_path / "garbage.unknown"
        f.write_bytes(b"\xff\xfe\xfd")  # invalid for all text parsers
        with pytest.raises(CasConfParseError):
            parse(f)


# ---------------------------------------------------------------------------
# casconf/registry.py  (TOML writer — lines 182-186)
# ---------------------------------------------------------------------------


class TestRegistryTomlWriter:
    """Covers registry.py lines 182-186 (_write_toml)."""

    def test_toml_output_is_written(self, tmp_path):
        from casconf.writer import write

        dest = tmp_path / "out.toml"
        write({"name": "casconf", "version": "1.0"}, output=dest, fmt="toml")
        assert dest.exists()
        content = dest.read_text(encoding="utf-8")
        assert "casconf" in content


class TestRegistryTomlParser:
    """Covers registry.py lines 136-141 (_parse_toml)."""

    def test_parses_toml_file(self, tmp_path):
        from casconf.parser import parse

        f = tmp_path / "config.toml"
        f.write_text(
            '[database]\nhost = "localhost"\nport = 5432\n',
            encoding="utf-8",
        )
        result = parse(f)
        assert result["database"]["host"] == "localhost"


# ---------------------------------------------------------------------------
# casconf/registry.py  (optional dep ImportError paths)
# ---------------------------------------------------------------------------


class TestRegistryOptionalDepErrors:
    """Verify helpful ImportError messages when optional deps are absent."""

    @staticmethod
    def _blocking_import(blocked_name: str):
        """Return an ``__import__`` replacement that blocks *blocked_name*."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == blocked_name:
                raise ImportError(f"No module named '{blocked_name}'")
            return real_import(name, *args, **kwargs)

        return fake_import

    def test_parse_yaml_missing_pyyaml(self, tmp_path, monkeypatch):
        import builtins

        import casconf.registry as reg_module

        f = tmp_path / "config.yaml"
        f.write_text("key: value\n", encoding="utf-8")
        monkeypatch.setattr(builtins, "__import__", self._blocking_import("yaml"))
        with pytest.raises(ImportError, match="casconf\\[yaml\\]"):
            reg_module._parse_yaml(f)

    def test_write_yaml_missing_pyyaml(self, monkeypatch):
        import builtins
        import io

        import casconf.registry as reg_module

        monkeypatch.setattr(builtins, "__import__", self._blocking_import("yaml"))
        with pytest.raises(ImportError, match="casconf\\[yaml\\]"):
            reg_module._write_yaml({"k": "v"}, io.StringIO())

    def test_write_toml_missing_tomli_w(self, monkeypatch):
        import builtins
        import io

        import casconf.registry as reg_module

        monkeypatch.setattr(builtins, "__import__", self._blocking_import("tomli_w"))
        with pytest.raises(ImportError, match="casconf\\[toml\\]"):
            reg_module._write_toml({"k": "v"}, io.StringIO())


class TestCliConfigureLogging:
    """Covers cli.py line 119 (verbose branch)."""

    def test_verbose_calls_basicconfig_with_debug(self, monkeypatch):
        import logging

        from casconf.cli import _configure_logging

        captured: list[int] = []

        def fake_basicconfig(**kwargs: object) -> None:
            captured.append(kwargs.get("level"))  # type: ignore[arg-type]

        monkeypatch.setattr(logging, "basicConfig", fake_basicconfig)
        _configure_logging(verbose=True)
        assert captured == [logging.DEBUG]


class TestCliUnexpectedException:
    """Covers cli.py lines 204-209 (bare except branch)."""

    def test_unexpected_exception_returns_1(self, tmp_path, monkeypatch):
        import yaml

        from casconf import cli

        dc = tmp_path / "casconf.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [str(FIXTURES / "base")],
                    "patterns": ["config.json"],
                }
            ),
            encoding="utf-8",
        )

        # Patch write to raise an unexpected (non-CasConf) exception
        # Must patch the name as imported in casconf.cli
        import casconf.cli as cli_module

        monkeypatch.setattr(
            cli_module,
            "write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("unexpected")),
        )

        rc = cli.main(["--discovery-config", str(dc)])
        assert rc == 1


class TestMergeConfigsWithDiscoveryConfigObject:
    """Covers api.py (DiscoveryConfig branch in merge_configs())."""

    def test_merge_configs_accepts_discovery_config_object(self):
        from casconf import merge_configs
        from casconf.discovery import DiscoveryConfig

        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        result = merge_configs(discovery_config=dc)
        assert isinstance(result, dict)
        assert "database" in result


# ---------------------------------------------------------------------------
# Third-level fixture key
# ---------------------------------------------------------------------------


class TestThirdLevelFixtureKey:
    """Fixture base/config.json has a three-level key; verify it survives
    deep-merge when override does not touch it."""

    def test_third_level_key_preserved_after_deep_merge(self, tmp_path, capsys):
        """database.credentials.username survives a deep merge with
        an override that only changes database.port."""
        import json

        import yaml

        from casconf.cli import main

        dc = tmp_path / "casconf.yaml"
        dc.write_text(
            yaml.dump(
                {
                    "directories": [
                        str(FIXTURES / "base"),
                        str(FIXTURES / "override"),
                    ],
                    "patterns": ["config.*"],
                }
            ),
            encoding="utf-8",
        )
        rc = main(["--discovery-config", str(dc)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        # Third-level key from base should survive merge
        assert data["database"]["credentials"]["username"] == "admin"
        # Override still wins for the port
        assert data["database"]["port"] == 5433


# ---------------------------------------------------------------------------
# _get_version uses PackageNotFoundError
# ---------------------------------------------------------------------------


class TestGetVersion:
    """_get_version falls back gracefully when package is not found."""

    def test_returns_fallback_on_package_not_found(self, monkeypatch):
        from importlib.metadata import PackageNotFoundError

        def raise_not_found(name: str) -> str:
            raise PackageNotFoundError(name)

        monkeypatch.setattr(
            "importlib.metadata.version",
            raise_not_found,
        )
        from casconf.cli import _get_version

        assert _get_version() == "casconf (version unknown)"

    def test_returns_version_string_when_installed(self):
        from casconf.cli import _get_version

        v = _get_version()
        assert v.startswith("casconf ")
