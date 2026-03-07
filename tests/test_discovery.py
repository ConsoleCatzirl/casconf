"""Tests for casconf.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from casconf.discovery import DiscoveryConfig, discover
from casconf.exceptions import CasConfConfigError

# Path to the test fixtures directory
FIXTURES = Path(__file__).parent / "fixtures"


class TestDiscoveryConfigConstruction:
    """DiscoveryConfig constructor validation."""

    def test_basic_construction(self):
        dc = DiscoveryConfig(
            directories=["/tmp"],
            patterns=["*.json"],
        )
        assert dc.patterns == ["*.json"]
        assert dc.merge_strategy == "deep"

    def test_directories_converted_to_path_objects(self):
        dc = DiscoveryConfig(
            directories=["/tmp", "/etc"],
            patterns=["config.json"],
        )
        for d in dc.directories:
            assert isinstance(d, Path)

    def test_tilde_expanded_in_directory(self):
        dc = DiscoveryConfig(
            directories=["~"],
            patterns=["*.json"],
        )
        assert "~" not in str(dc.directories[0])

    def test_custom_merge_strategy(self):
        dc = DiscoveryConfig(
            directories=["/tmp"],
            patterns=["*.yaml"],
            merge_strategy="shallow",
        )
        assert dc.merge_strategy == "shallow"

    def test_invalid_merge_strategy_raises(self):
        with pytest.raises(CasConfConfigError, match="merge_strategy"):
            DiscoveryConfig(
                directories=["/tmp"],
                patterns=["*.json"],
                merge_strategy="invalid",
            )

    def test_empty_directories_raises(self):
        with pytest.raises(CasConfConfigError, match="directories"):
            DiscoveryConfig(directories=[], patterns=["*.json"])

    def test_empty_patterns_raises(self):
        with pytest.raises(CasConfConfigError, match="patterns"):
            DiscoveryConfig(directories=["/tmp"], patterns=[])


class TestDiscoveryConfigFromDict:
    """DiscoveryConfig.from_dict() constructor."""

    def test_round_trip(self):
        data = {
            "directories": ["/tmp"],
            "patterns": ["config.json"],
            "merge_strategy": "shallow",
        }
        dc = DiscoveryConfig.from_dict(data)
        assert dc.patterns == ["config.json"]
        assert dc.merge_strategy == "shallow"

    def test_missing_directories_raises(self):
        with pytest.raises(CasConfConfigError, match="directories"):
            DiscoveryConfig.from_dict({"patterns": ["*.json"]})

    def test_missing_patterns_raises(self):
        with pytest.raises(CasConfConfigError, match="patterns"):
            DiscoveryConfig.from_dict({"directories": ["/tmp"]})

    def test_merge_strategy_defaults_to_deep(self):
        dc = DiscoveryConfig.from_dict({"directories": ["/tmp"], "patterns": ["*.json"]})
        assert dc.merge_strategy == "deep"


class TestDiscover:
    """discover() integration tests using fixture directories."""

    def test_finds_json_file(self):
        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "base")],
            patterns=["config.json"],
        )
        found = discover(dc)
        assert len(found) == 1
        assert found[0].name == "config.json"

    def test_finds_yaml_file(self):
        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "override")],
            patterns=["config.yaml"],
        )
        found = discover(dc)
        assert len(found) == 1
        assert found[0].name == "config.yaml"

    def test_multiple_directories_ordered(self):
        dc = DiscoveryConfig(
            directories=[
                str(FIXTURES / "base"),
                str(FIXTURES / "override"),
            ],
            patterns=["config.*"],
        )
        found = discover(dc)
        # base first, then override
        assert len(found) == 2
        dirs = [f.parent.name for f in found]
        assert dirs[0] == "base"
        assert dirs[1] == "override"

    def test_missing_directory_skipped_with_warning(self):
        dc = DiscoveryConfig(
            directories=[
                "/nonexistent/path/that/does/not/exist",
                str(FIXTURES / "base"),
            ],
            patterns=["config.json"],
        )
        found = discover(dc)
        assert len(found) == 1

    def test_empty_directory_returns_empty_list(self, tmp_path):
        dc = DiscoveryConfig(
            directories=[str(tmp_path)],
            patterns=["config.json"],
        )
        found = discover(dc)
        assert found == []

    def test_glob_pattern_in_filename(self):
        dc = DiscoveryConfig(
            directories=[str(FIXTURES / "base")],
            patterns=["*.json"],
        )
        found = discover(dc)
        assert any(f.suffix == ".json" for f in found)


class TestDiscoveryConfigFromFile:
    """DiscoveryConfig.from_file() edge cases."""

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "dc.xml"
        p.write_text("<config/>", encoding="utf-8")
        with pytest.raises(CasConfConfigError, match="Unsupported"):
            DiscoveryConfig.from_file(p)

    def test_bad_yaml_content_raises(self, tmp_path):
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
    """DiscoveryConfig.__eq__() comparison behaviour."""

    def test_eq_with_non_discovery_config_returns_not_implemented(self):
        dc = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        result = dc.__eq__("not a DiscoveryConfig")
        assert result is NotImplemented

    def test_eq_same_values_returns_true(self):
        dc1 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        dc2 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"])
        assert dc1 == dc2

    def test_eq_different_strategy_returns_false(self):
        dc1 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"], merge_strategy="deep")
        dc2 = DiscoveryConfig(directories=["/tmp"], patterns=["*.json"], merge_strategy="shallow")
        assert dc1 != dc2


class TestDiscoverPathNotDir:
    """discover() skips entries that are files rather than directories."""

    def test_file_path_used_as_directory_is_skipped(self, tmp_path):
        # Use a regular file as a directory — should be warned and skipped
        f = tmp_path / "not_a_dir.json"
        f.write_text("{}", encoding="utf-8")
        dc = DiscoveryConfig(directories=[str(f)], patterns=["*.json"])
        found = discover(dc)
        assert found == []
