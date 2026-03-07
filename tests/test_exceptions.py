"""Tests for casconf.exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from casconf.exceptions import (
    CasConfConfigError,
    CasConfError,
    CasConfMergeError,
    CasConfParseError,
    CasConfWriteError,
)


class TestExceptionHierarchy:
    """All CasConf exceptions derive from CasConfError."""

    def test_config_error_is_casconf_error(self):
        assert issubclass(CasConfConfigError, CasConfError)

    def test_parse_error_is_casconf_error(self):
        assert issubclass(CasConfParseError, CasConfError)

    def test_merge_error_is_casconf_error(self):
        assert issubclass(CasConfMergeError, CasConfError)

    def test_write_error_is_casconf_error(self):
        assert issubclass(CasConfWriteError, CasConfError)

    def test_casconf_error_is_exception(self):
        assert issubclass(CasConfError, Exception)


class TestCasConfParseError:
    """CasConfParseError stores the offending file path."""

    def test_stores_path_as_path_object(self):
        exc = CasConfParseError("boom", "/tmp/bad.json")
        assert exc.path == Path("/tmp/bad.json")

    def test_stores_path_when_given_path_object(self):
        p = Path("/etc/app/config.yaml")
        exc = CasConfParseError("boom", p)
        assert exc.path == p

    def test_message_is_preserved(self):
        exc = CasConfParseError("could not parse", "cfg.json")
        assert str(exc) == "could not parse"

    def test_catchable_as_casconf_error(self):
        with pytest.raises(CasConfError):
            raise CasConfParseError("x", "f.json")
