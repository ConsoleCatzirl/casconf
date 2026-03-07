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
