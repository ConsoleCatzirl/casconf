"""CascConf parser engine.

Reads a configuration file from disk and returns its contents as a
plain Python ``dict``.  Format detection is extension-based with a
fallback parser chain for files whose extension is unknown or absent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from cascconf.exceptions import CascConfParseError
from cascconf.registry import registry

logger = logging.getLogger(__name__)


def parse(path: Path) -> dict[str, Any]:
    """Read *path* and return its contents as a dict.

    Format is detected from the file extension.  If the extension is
    unrecognised, each registered parser is tried in turn until one
    succeeds.  An empty file returns ``{}``.

    Args:
        path: The configuration file to parse.

    Returns:
        A ``dict`` representing the parsed configuration.  An empty
        file returns an empty dict.

    Raises:
        CascConfParseError: If the file cannot be read or no parser
            succeeds.
    """
    if not path.exists():
        raise CascConfParseError(
            f"Configuration file not found: {path}",
            path,
        )

    suffix = path.suffix.lower()
    parser_fn = registry.get_parser(suffix)

    if parser_fn is not None:
        logger.debug(
            "Parsing %s with %s parser",
            path,
            suffix or "unknown",
        )
        try:
            return parser_fn(path)
        except Exception as exc:
            raise CascConfParseError(
                f"Failed to parse {path}: {exc}",
                path,
            ) from exc

    # Fallback: try every registered parser
    logger.debug(
        "Unknown extension %r for %s; trying all parsers",
        suffix,
        path,
    )
    last_exc: Exception | None = None
    for ext in registry.supported_extensions:
        try:
            result = registry.get_parser(ext)(path)  # type: ignore[misc]
            logger.debug(
                "Parsed %s successfully with %s parser",
                path,
                ext,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            last_exc = exc

    raise CascConfParseError(
        f"No parser could read {path}"
        + (f": {last_exc}" if last_exc else ""),
        path,
    )
