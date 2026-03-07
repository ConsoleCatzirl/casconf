"""CascConf writer engine.

Serialises a merged configuration dict and writes it either to a
file or to a text stream (stdout by default).

Supported output formats: ``'json'`` (default), ``'yaml'``, ``'toml'``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from cascconf.exceptions import CascConfWriteError
from cascconf.registry import registry

logger = logging.getLogger(__name__)

_DEFAULT_FORMAT = "json"


def write(
    data: dict[str, Any],
    output: str | Path | None = None,
    fmt: str = _DEFAULT_FORMAT,
) -> None:
    """Serialise *data* and write to *output* (or stdout).

    Args:
        data: The merged configuration dict to write.
        output: Destination file path.  Pass ``None`` (default) to
            write to stdout.
        fmt: Output format name.  One of ``'json'``, ``'yaml'``,
            ``'toml'``.  Defaults to ``'json'``.

    Raises:
        CascConfWriteError: If the format is unsupported or the file
            cannot be written.
    """
    writer_fn = registry.get_writer(fmt.lower())
    if writer_fn is None:
        raise CascConfWriteError(f"Unsupported output format {fmt!r}. Supported: {registry.supported_formats}")

    if output is None:
        logger.debug("Writing %s output to stdout", fmt)
        writer_fn(data, sys.stdout)  # type: ignore[arg-type]
        return

    dest = Path(output)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as fh:
            logger.debug("Writing %s output to %s", fmt, dest)
            writer_fn(data, fh)
    except OSError as exc:
        raise CascConfWriteError(f"Failed to write output to {dest}: {exc}") from exc

    logger.info("Output written to %s", dest)
