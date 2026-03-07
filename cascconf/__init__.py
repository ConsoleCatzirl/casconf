"""CascConf — cascading configuration manager.

This is the top-level package.  Import the public API from here::

    from cascconf import merge_configs, validate_config, DiscoveryConfig

The complete API reference is available in ``API.md``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from cascconf.discovery import DiscoveryConfig
from cascconf.exceptions import (
    CascConfConfigError,
    CascConfError,
    CascConfMergeError,
    CascConfParseError,
    CascConfValidationError,
    CascConfWriteError,
)

_ENV_DISCOVERY = "CASCCONF_DISCOVERY"
_DEFAULT_DISCOVERY = "cascconf.yaml"

__all__ = [
    "merge_configs",
    "validate_config",
    "DiscoveryConfig",
    "CascConfError",
    "CascConfConfigError",
    "CascConfParseError",
    "CascConfMergeError",
    "CascConfWriteError",
    "CascConfValidationError",
]


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
            value of ``$CASCCONF_DISCOVERY`` (falling back to
            ``'cascconf.yaml'``).
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
        CascConfConfigError: If the discovery configuration is
            invalid.
        CascConfParseError: If a configuration file cannot be parsed.
        CascConfMergeError: If configurations cannot be merged.
        CascConfWriteError: If the output file cannot be written.

    Examples::

        # Return merged config as a dict
        config = merge_configs()

        # Write to a file
        merge_configs(
            discovery_config='./cascconf.yaml',
            output='./merged.json',
        )
    """
    from cascconf.cli import run
    from cascconf.writer import write

    if discovery_config is None:
        discovery_config = os.environ.get(
            _ENV_DISCOVERY, _DEFAULT_DISCOVERY
        )

    merged = run(
        discovery_config=discovery_config,
        output=None,  # Always collect the dict first
        output_format=output_format,
        log_level=log_level,
    )

    if output is not None:
        write(merged, output=output, fmt=output_format)
        return None

    return merged


def validate_config(
    config: dict[str, Any],
    schema: str | Path | dict[str, Any],
) -> None:
    """Validate *config* against a JSON Schema.

    Args:
        config: The configuration dict to validate.
        schema: Path to a JSON Schema file, or an inline schema dict.

    Raises:
        CascConfValidationError: If the configuration does not match
            the schema.
        ImportError: If ``jsonschema`` is not installed.  Install it
            with ``pip install cascconf[validation]``.
    """
    try:
        import jsonschema
    except ImportError as exc:
        raise ImportError(
            "Schema validation requires the 'jsonschema' package. "
            "Install it with: pip install cascconf[validation]"
        ) from exc

    if not isinstance(schema, dict):
        # Load schema from file
        from cascconf.parser import parse as _parse

        schema = _parse(Path(schema))

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(
        validator.iter_errors(config), key=lambda e: list(e.path)
    )
    if errors:
        messages = [e.message for e in errors]
        raise CascConfValidationError(
            f"Configuration validation failed with "
            f"{len(messages)} error(s): "
            + "; ".join(messages),
            errors=messages,
        )
