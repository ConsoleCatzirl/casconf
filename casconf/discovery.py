"""CasConf discovery engine.

Responsible for locating configuration files based on a
:class:`DiscoveryConfig` and returning an ordered list of
:class:`~pathlib.Path` objects ready for parsing.

The :class:`DiscoveryConfig` object is also the public data class
that users construct (or load from a file) to describe *where* and
*what* to scan.
"""

from __future__ import annotations

import glob as _glob
import logging
import os
from pathlib import Path
from typing import Any

from casconf.exceptions import CasConfConfigError

logger = logging.getLogger(__name__)

_VALID_STRATEGIES = frozenset({"deep", "shallow"})


class DiscoveryConfig:
    """Configuration for the CasConf discovery engine.

    Directories are scanned in the order they are listed; later
    entries take precedence over earlier ones during merging.

    Attributes:
        directories: Ordered list of resolved directory paths to scan.
        patterns: File name patterns to match within each directory.
            Supports glob wildcards (``*``, ``?``, ``[…]``).
        merge_strategy: Merge strategy to use (``'deep'`` or
            ``'shallow'``).
    """

    def __init__(
        self,
        directories: list[str | Path],
        patterns: list[str],
        merge_strategy: str = "deep",
    ) -> None:
        """Initialise a DiscoveryConfig.

        Args:
            directories: Ordered list of directories to scan.
                Supports ``~`` expansion and environment variables.
                Glob patterns in paths are expanded at scan time.
            patterns: File name patterns to match.
            merge_strategy: One of ``'deep'`` (default) or
                ``'shallow'``.

        Raises:
            CasConfConfigError: If *merge_strategy* is invalid or
                *directories*/*patterns* are empty.
        """
        if not directories:
            raise CasConfConfigError("'directories' must contain at least one entry.")
        if not patterns:
            raise CasConfConfigError("'patterns' must contain at least one entry.")
        if merge_strategy not in _VALID_STRATEGIES:
            raise CasConfConfigError(f"Invalid merge_strategy {merge_strategy!r}. Must be one of: {sorted(_VALID_STRATEGIES)}")

        self.directories: list[Path] = [Path(os.path.expandvars(os.path.expanduser(str(d)))) for d in directories]
        self.patterns: list[str] = list(patterns)
        self.merge_strategy: str = merge_strategy

    # ------------------------------------------------------------------
    # Class-method constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> DiscoveryConfig:
        """Load a :class:`DiscoveryConfig` from a YAML, JSON, or TOML file.

        Args:
            path: Path to the discovery configuration file.

        Returns:
            A new :class:`DiscoveryConfig` instance.

        Raises:
            CasConfConfigError: If the file cannot be read or is
                missing required keys.
        """
        from casconf.registry import registry

        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise CasConfConfigError(f"Discovery configuration file not found: {resolved}")
        parser = registry.get_parser(resolved.suffix)
        if parser is None:
            raise CasConfConfigError(f"Unsupported discovery configuration format: {resolved.suffix!r}")
        try:
            data: dict[str, Any] = parser(resolved)
        except Exception as exc:
            raise CasConfConfigError(f"Failed to read discovery configuration: {exc}") from exc
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveryConfig:
        """Create a :class:`DiscoveryConfig` from a plain dict.

        Args:
            data: Dictionary with keys ``'directories'``,
                ``'patterns'``, and optionally ``'merge_strategy'``.

        Returns:
            A new :class:`DiscoveryConfig` instance.

        Raises:
            CasConfConfigError: If required keys are missing.
        """
        for key in ("directories", "patterns"):
            if key not in data:
                raise CasConfConfigError(f"Missing required key in discovery configuration: {key!r}")
        return cls(
            directories=data["directories"],
            patterns=data["patterns"],
            merge_strategy=data.get("merge_strategy", "deep"),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"DiscoveryConfig("
            f"directories={self.directories!r}, "
            f"patterns={self.patterns!r}, "
            f"merge_strategy={self.merge_strategy!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DiscoveryConfig):
            return NotImplemented
        return (
            self.directories == other.directories
            and self.patterns == other.patterns
            and self.merge_strategy == other.merge_strategy
        )


# ---------------------------------------------------------------------------
# Discovery engine
# ---------------------------------------------------------------------------


def discover(config: DiscoveryConfig) -> list[Path]:
    """Scan directories and return an ordered list of matching files.

    Directories are scanned in order.  Within each directory every
    pattern is checked in order.  The returned list is de-duplicated
    while preserving the first-seen order.

    Missing or unreadable directories produce a warning and are
    skipped.

    Args:
        config: A :class:`DiscoveryConfig` describing where and what
            to scan.

    Returns:
        Ordered list of :class:`~pathlib.Path` objects, from lowest
        to highest priority.
    """
    found: list[Path] = []
    seen: set[Path] = set()

    for raw_dir in config.directories:
        # Expand glob patterns in the directory path itself
        expanded_dirs = sorted(_glob.glob(str(raw_dir))) or [str(raw_dir)]
        for dir_str in expanded_dirs:
            directory = Path(dir_str)
            if not directory.exists():
                logger.warning(
                    "Directory does not exist, skipping: %s",
                    directory,
                )
                continue
            if not directory.is_dir():
                logger.warning(
                    "Path is not a directory, skipping: %s",
                    directory,
                )
                continue

            for pattern in config.patterns:
                for match in sorted(directory.glob(pattern)):
                    if match.is_file() and match not in seen:
                        logger.debug("Discovered: %s", match)
                        found.append(match)
                        seen.add(match)

    logger.info(
        "Discovery complete: %d file(s) found across %d director(ies) using %d pattern(s)",
        len(found),
        len(config.directories),
        len(config.patterns),
    )
    return found
