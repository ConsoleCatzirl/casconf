"""Tests for casconf.api (public merge_configs API)."""

from __future__ import annotations

import json
from pathlib import Path

from casconf import merge_configs
from casconf.discovery import DiscoveryConfig

# Path to the test fixtures directory
FIXTURES = Path(__file__).parent / "fixtures"


class TestMergeConfigsPublicApi:
    """merge_configs() return value and output-file behaviour."""

    def test_returns_dict_when_no_output(self, tmp_path):
        """merge_configs() returns dict when output=None."""
        import yaml

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
        """merge_configs(None) uses CASCONF_DISCOVERY env var."""
        import yaml

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
        monkeypatch.setenv("CASCONF_DISCOVERY", str(dc))
        result = merge_configs(discovery_config=None)
        assert isinstance(result, dict)


class TestMergeConfigsWithDiscoveryConfigObject:
    """merge_configs() accepts a DiscoveryConfig object directly."""

    def test_merge_configs_accepts_discovery_config_object(self):
        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        result = merge_configs(discovery_config=dc)
        assert isinstance(result, dict)
        assert "database" in result


class TestThirdLevelFixtureKey:
    """Three-level nested keys survive a deep merge end-to-end."""

    def test_third_level_key_preserved_after_deep_merge(self, tmp_path, capsys):
        """database.credentials.username survives a deep merge with
        an override that only changes database.port."""
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
