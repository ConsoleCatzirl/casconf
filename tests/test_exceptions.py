"""Tests for cascconf.exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from cascconf.exceptions import (
    CascConfConfigError,
    CascConfError,
    CascConfMergeError,
    CascConfParseError,
    CascConfWriteError,
)


class TestExceptionHierarchy:
    """All CascConf exceptions derive from CascConfError."""

    def test_config_error_is_cascconf_error(self):
        assert issubclass(CascConfConfigError, CascConfError)

    def test_parse_error_is_cascconf_error(self):
        assert issubclass(CascConfParseError, CascConfError)

    def test_merge_error_is_cascconf_error(self):
        assert issubclass(CascConfMergeError, CascConfError)

    def test_write_error_is_cascconf_error(self):
        assert issubclass(CascConfWriteError, CascConfError)

    def test_cascconf_error_is_exception(self):
        assert issubclass(CascConfError, Exception)


class TestCascConfParseError:
    """CascConfParseError stores the offending file path."""

    def test_stores_path_as_path_object(self):
        exc = CascConfParseError("boom", "/tmp/bad.json")
        assert exc.path == Path("/tmp/bad.json")

    def test_stores_path_when_given_path_object(self):
        p = Path("/etc/app/config.yaml")
        exc = CascConfParseError("boom", p)
        assert exc.path == p

    def test_message_is_preserved(self):
        exc = CascConfParseError("could not parse", "cfg.json")
        assert str(exc) == "could not parse"

    def test_catchable_as_cascconf_error(self):
        with pytest.raises(CascConfError):
            raise CascConfParseError("x", "f.json")
