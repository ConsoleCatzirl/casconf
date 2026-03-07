"""CascConf — cascading configuration manager.

This is the top-level package.  Import the public API from here::

    from cascconf import merge_configs, validate_config, DiscoveryConfig

The complete API reference is available in ``API.md``.
"""

from __future__ import annotations

from cascconf.api import merge_configs, validate_config
from cascconf.discovery import DiscoveryConfig
from cascconf.exceptions import (
    CascConfConfigError,
    CascConfError,
    CascConfMergeError,
    CascConfParseError,
    CascConfValidationError,
    CascConfWriteError,
)

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
