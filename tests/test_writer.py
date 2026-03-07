"""Tests for casconf.writer."""

from __future__ import annotations

import json

import pytest

from casconf.exceptions import CasConfWriteError
from casconf.writer import write


class TestWriteToFile:
    """write() with file output."""

    def test_writes_json_to_file(self, tmp_path):
        dest = tmp_path / "out.json"
        write({"key": "value"}, output=dest, fmt="json")
        assert dest.exists()
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data == {"key": "value"}

    def test_creates_parent_directories(self, tmp_path):
        dest = tmp_path / "nested" / "dir" / "out.json"
        write({"a": 1}, output=dest, fmt="json")
        assert dest.exists()

    def test_writes_yaml_to_file(self, tmp_path):
        import yaml

        dest = tmp_path / "out.yaml"
        write({"host": "localhost"}, output=dest, fmt="yaml")
        data = yaml.safe_load(dest.read_text(encoding="utf-8"))
        assert data["host"] == "localhost"

    def test_unsupported_format_raises_write_error(self, tmp_path):
        dest = tmp_path / "out.xml"
        with pytest.raises(CasConfWriteError, match="Unsupported"):
            write({"a": 1}, output=dest, fmt="xml")

    def test_json_output_is_sorted_and_indented(self, tmp_path):
        dest = tmp_path / "out.json"
        write({"b": 2, "a": 1}, output=dest, fmt="json")
        raw = dest.read_text(encoding="utf-8")
        # Sorted keys: "a" should appear before "b"
        assert raw.index('"a"') < raw.index('"b"')
        # Indented: should contain newlines
        assert "\n" in raw


class TestWriteToStdout:
    """write() with stdout output (output=None)."""

    def test_writes_json_to_stdout(self, capsys):
        write({"hello": "world"}, output=None, fmt="json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data == {"hello": "world"}

    def test_writes_yaml_to_stdout(self, capsys):
        import yaml

        write({"host": "localhost"}, output=None, fmt="yaml")
        captured = capsys.readouterr()
        data = yaml.safe_load(captured.out)
        assert data["host"] == "localhost"

    def test_unsupported_format_raises_write_error(self):
        with pytest.raises(CasConfWriteError, match="Unsupported"):
            write({"a": 1}, output=None, fmt="csv")


class TestWriteEmptyDict:
    """write() handles an empty configuration dict."""

    def test_empty_dict_json(self, tmp_path):
        dest = tmp_path / "empty.json"
        write({}, output=dest, fmt="json")
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data == {}
