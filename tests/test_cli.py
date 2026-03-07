"""Tests for casconf.cli (argument parsing and orchestration)."""

from __future__ import annotations

import json
from pathlib import Path

from casconf.cli import _build_parser, main

# Path to the test fixtures directory
FIXTURES = Path(__file__).parent / "fixtures"


def _make_discovery_yaml(
    tmp_path: Path,
    dirs: list[str],
    patterns: list[str],
    strategy: str = "deep",
) -> Path:
    """Write a temporary casconf.yaml and return its path."""
    import yaml

    cfg = {
        "directories": dirs,
        "patterns": patterns,
        "merge_strategy": strategy,
    }
    p = tmp_path / "casconf.yaml"
    p.write_text(yaml.dump(cfg), encoding="utf-8")
    return p


class TestArgumentParser:
    """_build_parser() produces correct defaults."""

    def test_default_output_is_none(self):
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.output is None

    def test_default_format_is_json(self):
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.output_format == "json"

    def test_output_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--output", "/tmp/out.json"])
        assert args.output == "/tmp/out.json"

    def test_format_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--format", "yaml"])
        assert args.output_format == "yaml"

    def test_verbose_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_discovery_config_flag(self, tmp_path):
        p = str(tmp_path / "custom.yaml")
        parser = _build_parser()
        args = parser.parse_args(["--discovery-config", p])
        assert args.discovery_config == p


class TestArgumentParserEnvVars:
    """_build_parser() reads defaults from environment variables."""

    def test_env_output_sets_default(self, monkeypatch):
        monkeypatch.setenv("CASCONF_OUTPUT", "/tmp/env-out.json")
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.output == "/tmp/env-out.json"

    def test_env_format_sets_default(self, monkeypatch):
        monkeypatch.setenv("CASCONF_FORMAT", "yaml")
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.output_format == "yaml"

    def test_env_verbose_sets_default(self, monkeypatch):
        monkeypatch.setenv("CASCONF_VERBOSE", "1")
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.verbose is True

    def test_env_verbose_true_string(self, monkeypatch):
        monkeypatch.setenv("CASCONF_VERBOSE", "true")
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.verbose is True

    def test_env_verbose_false_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CASCONF_VERBOSE", raising=False)
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.verbose is False

    def test_cli_flag_overrides_env_output(self, monkeypatch):
        monkeypatch.setenv("CASCONF_OUTPUT", "/tmp/env-out.json")
        parser = _build_parser()
        args = parser.parse_args(["--output", "/tmp/cli-out.json"])
        assert args.output == "/tmp/cli-out.json"

    def test_cli_flag_overrides_env_format(self, monkeypatch):
        monkeypatch.setenv("CASCONF_FORMAT", "yaml")
        parser = _build_parser()
        args = parser.parse_args(["--format", "toml"])
        assert args.output_format == "toml"


class TestMainCli:
    """main() end-to-end tests."""

    def test_merges_single_json_config_to_stdout(self, tmp_path, capsys):
        dc = _make_discovery_yaml(
            tmp_path,
            dirs=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        rc = main(["--discovery-config", str(dc)])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["database"]["host"] == "localhost"

    def test_writes_output_to_file(self, tmp_path):
        dc = _make_discovery_yaml(
            tmp_path,
            dirs=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        out_file = tmp_path / "merged.json"
        rc = main(
            [
                "--discovery-config",
                str(dc),
                "--output",
                str(out_file),
            ]
        )
        assert rc == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert "database" in data

    def test_returns_1_on_missing_discovery_config(self, tmp_path):
        rc = main(
            [
                "--discovery-config",
                str(tmp_path / "nonexistent.yaml"),
            ]
        )
        assert rc == 1

    def test_deep_merge_two_directories(self, tmp_path, capsys):
        dc = _make_discovery_yaml(
            tmp_path,
            dirs=[
                str(FIXTURES / "base"),
                str(FIXTURES / "override"),
            ],
            patterns=["config.*"],
        )
        rc = main(["--discovery-config", str(dc)])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        # base has port=5432; override has port=5433
        assert data["database"]["port"] == 5433
        # base has host; override does not -> should be preserved
        assert data["database"]["host"] == "localhost"


class TestConfigureLogging:
    """_configure_logging() sets up the root logger correctly."""

    def test_verbose_calls_basicconfig_with_debug(self, monkeypatch):
        import logging

        from casconf.cli import _configure_logging

        captured: list[int] = []

        def fake_basicconfig(**kwargs: object) -> None:
            captured.append(kwargs.get("level"))  # type: ignore[arg-type]

        monkeypatch.setattr(logging, "basicConfig", fake_basicconfig)
        _configure_logging(verbose=True)
        assert captured == [logging.DEBUG]


class TestUnexpectedException:
    """main() returns exit code 1 on unexpected (non-CasConf) exceptions."""

    def test_unexpected_exception_returns_1(self, tmp_path, monkeypatch):
        import yaml

        import casconf.cli as cli_module

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
        monkeypatch.setattr(
            cli_module,
            "write",
            lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("unexpected")),
        )

        rc = cli_module.main(["--discovery-config", str(dc)])
        assert rc == 1


class TestGetVersion:
    """_get_version() falls back gracefully when the package is not installed."""

    def test_returns_fallback_on_package_not_found(self, monkeypatch):
        from importlib.metadata import PackageNotFoundError

        def raise_not_found(name: str) -> str:
            raise PackageNotFoundError(name)

        monkeypatch.setattr("importlib.metadata.version", raise_not_found)
        from casconf.cli import _get_version

        assert _get_version() == "casconf (version unknown)"

    def test_returns_version_string_when_installed(self):
        from casconf.cli import _get_version

        v = _get_version()
        assert v.startswith("casconf ")
