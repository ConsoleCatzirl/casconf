"""CascConf exception hierarchy.

All exceptions raised by CascConf are subclasses of :class:`CascConfError`.
Import from this module or from the top-level ``cascconf`` package.

Example::

    from cascconf.exceptions import CascConfParseError

    try:
        config = merge_configs()
    except CascConfParseError as exc:
        print(f"Could not parse {exc.path}: {exc}")
"""

from __future__ import annotations

from pathlib import Path


class CascConfError(Exception):
    """Base exception for all CascConf errors."""


class CascConfConfigError(CascConfError):
    """Raised when the discovery configuration is invalid.

    This covers missing required keys, invalid values, and
    unreadable discovery configuration files.
    """


class CascConfParseError(CascConfError):
    """Raised when a configuration file cannot be parsed.

    Attributes:
        path: The path to the file that failed to parse.
    """

    def __init__(self, message: str, path: Path | str) -> None:
        super().__init__(message)
        self.path: Path = Path(path)


class CascConfMergeError(CascConfError):
    """Raised when configurations cannot be merged."""


class CascConfWriteError(CascConfError):
    """Raised when the output cannot be written.

    This covers permission-denied errors, invalid output paths,
    and unsupported output formats.
    """
