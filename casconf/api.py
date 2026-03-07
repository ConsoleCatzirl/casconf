"""CasConf public API implementations.

:func:`merge_configs` lives here so that ``casconf/__init__.py``
stays thin.  It is re-exported from the top-level package::

    from casconf import merge_configs
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from casconf.discovery import DiscoveryConfig, discover
from casconf.merger import merge
from casconf.parser import parse
from casconf.writer import write

_ENV_DISCOVERY = "CASCONF_DISCOVERY"
_DEFAULT_DISCOVERY = "casconf.yaml"


def merge_configs(
    discovery_config: str | Path | DiscoveryConfig | None = None,
    output: str | Path | None = None,
    output_format: str = "json",
    log_level: int = logging.WARNING,
) -> dict[str, Any] | None:
    """Discover, parse, and deep-merge configuration files.

    Args:
        discovery_config: Path to a discovery configuration file, a
            :class:`DiscoveryConfig` object, or ``None`` to use the
            value of ``$CASCONF_DISCOVERY`` (falling back to
            ``'casconf.yaml'``).
        output: Destination file path.  If ``None`` (default), the
            merged dict is returned and nothing is written to disk.
        output_format: Serialisation format used when *output* is not
            ``None``.  One of ``'json'`` (default), ``'yaml'``,
            ``'toml'``.
        log_level: Python :mod:`logging` level for this run.  Use
            ``logging.DEBUG`` for verbose output.

    Returns:
        The merged configuration dict when *output* is ``None``;
        ``None`` when *output* is specified (result written to file).

    Raises:
        CasConfConfigError: If the discovery configuration is
            invalid.
        CasConfParseError: If a configuration file cannot be parsed.
        CasConfMergeError: If configurations cannot be merged.
        CasConfWriteError: If the output file cannot be written.

    Examples::

        # Return merged config as a dict
        config = merge_configs()

        # Write to a file
        merge_configs(
            discovery_config='./casconf.yaml',
            output='./merged.json',
        )
    """
    logging.getLogger("casconf").setLevel(log_level)

    if discovery_config is None:
        discovery_config = os.environ.get(_ENV_DISCOVERY, _DEFAULT_DISCOVERY)

    if not isinstance(discovery_config, DiscoveryConfig):
        discovery_config = DiscoveryConfig.from_file(Path(discovery_config))

    paths = discover(discovery_config)
    configs = [parse(p) for p in paths]
    merged = merge(configs, strategy=discovery_config.merge_strategy, list_strategy=discovery_config.list_merge_strategy)

    if output is not None:
        write(merged, output=output, fmt=output_format)
        return None

    return merged
