"""Tests for casconf.registry (optional dependency error messages)."""

from __future__ import annotations

import pytest


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
