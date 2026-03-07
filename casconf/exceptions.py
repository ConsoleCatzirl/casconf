"""CasConf exception hierarchy.

All exceptions raised by CasConf are subclasses of :class:`CasConfError`.
Import from this module or from the top-level ``casconf`` package.

Example::

    from casconf.exceptions import CasConfParseError

    try:
        config = merge_configs()
    except CasConfParseError as exc:
        print(f"Could not parse {exc.path}: {exc}")
"""

from __future__ import annotations

from pathlib import Path


class CasConfError(Exception):
    """Base exception for all CasConf errors."""


class CasConfConfigError(CasConfError):
    """Raised when the discovery configuration is invalid.

    This covers missing required keys, invalid values, and
    unreadable discovery configuration files.
    """


class CasConfParseError(CasConfError):
    """Raised when a configuration file cannot be parsed.

    Attributes:
        path: The path to the file that failed to parse.
    """

    def __init__(self, message: str, path: Path | str) -> None:
        super().__init__(message)
        self.path: Path = Path(path)


class CasConfMergeError(CasConfError):
    """Raised when configurations cannot be merged."""


class CasConfWriteError(CasConfError):
    """Raised when the output cannot be written.

    This covers permission-denied errors, invalid output paths,
    and unsupported output formats.
    """
