"""Tests for casconf.merger."""

from __future__ import annotations

from typing import Any

import pytest

from casconf.merger import deep_merge, merge, shallow_merge


class TestDeepMerge:
    """Unit tests for deep_merge()."""

    def test_merges_top_level_scalars(self):
        result = deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_override_replaces_scalar(self):
        result = deep_merge({"key": "base"}, {"key": "override"})
        assert result["key"] == "override"

    def test_merges_nested_dicts(self):
        base = {"database": {"host": "localhost", "port": 5432}}
        override = {"database": {"port": 5433, "name": "mydb"}}

        result = deep_merge(base, override)

        assert result == {
            "database": {
                "host": "localhost",
                "port": 5433,
                "name": "mydb",
            }
        }

    def test_appends_lists(self):
        base = {"plugins": ["auth", "cache"]}
        override = {"plugins": ["metrics"]}

        result = deep_merge(base, override)

        assert result["plugins"] == ["auth", "cache", "metrics"]

    def test_does_not_mutate_base(self):
        base: dict[str, Any] = {"key": "base_value"}
        override: dict[str, Any] = {"key": "override_value"}

        deep_merge(base, override)

        assert base["key"] == "base_value"

    def test_does_not_mutate_override(self):
        base: dict[str, Any] = {"key": "base_value"}
        override: dict[str, Any] = {"key": "override_value"}

        deep_merge(base, override)

        assert override["key"] == "override_value"

    def test_empty_override_returns_copy_of_base(self):
        base = {"a": 1}
        result = deep_merge(base, {})
        assert result == {"a": 1}
        assert result is not base

    def test_empty_base_returns_copy_of_override(self):
        override = {"b": 2}
        result = deep_merge({}, override)
        assert result == {"b": 2}

    def test_deeply_nested_merge(self):
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 99}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 99, "d": 2}}}

    def test_new_key_in_override_is_added(self):
        base = {"x": 1}
        override = {"y": 2}
        result = deep_merge(base, override)
        assert result == {"x": 1, "y": 2}


class TestShallowMerge:
    """Unit tests for shallow_merge()."""

    def test_top_level_key_replaced(self):
        base = {"database": {"host": "a", "port": 1}}
        override = {"database": {"host": "b"}}
        result = shallow_merge(base, override)
        # Shallow: entire 'database' dict replaced
        assert result["database"] == {"host": "b"}

    def test_does_not_mutate_base(self):
        base: dict[str, Any] = {"a": 1}
        shallow_merge(base, {"a": 2})
        assert base["a"] == 1

    def test_new_keys_added(self):
        result = shallow_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}


class TestMerge:
    """Unit tests for the public merge() dispatcher."""

    def test_empty_list_returns_empty_dict(self):
        assert merge([]) == {}

    def test_single_config_returned_unchanged(self):
        result = merge([{"a": 1}])
        assert result == {"a": 1}

    def test_deep_strategy_is_default(self):
        configs = [
            {"db": {"host": "a", "port": 1}},
            {"db": {"port": 2}},
        ]
        result = merge(configs)
        assert result == {"db": {"host": "a", "port": 2}}

    def test_shallow_strategy_replaces_top_level(self):
        configs = [
            {"db": {"host": "a", "port": 1}},
            {"db": {"port": 2}},
        ]
        result = merge(configs, strategy="shallow")
        assert result == {"db": {"port": 2}}

    def test_invalid_strategy_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            merge([{"a": 1}], strategy="invalid")

    def test_multiple_configs_merged_left_to_right(self):
        configs = [{"a": 1}, {"b": 2}, {"c": 3}]
        result = merge(configs)
        assert result == {"a": 1, "b": 2, "c": 3}


class TestDeepMergeTypeConflict:
    """deep_merge() behaviour when base and override have incompatible types."""

    def test_type_conflict_override_wins(self):
        base = {"key": "a string"}
        override = {"key": {"nested": "dict"}}
        result = deep_merge(base, override)
        assert result["key"] == {"nested": "dict"}

    def test_type_conflict_logs_warning(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="casconf.merger"):
            deep_merge({"key": "string"}, {"key": 42})
        assert any("conflict" in r.message.lower() for r in caplog.records)
