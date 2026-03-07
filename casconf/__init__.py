"""CasConf — cascading configuration manager.

This is the top-level package.  Import the public API from here::

    from casconf import merge_configs, DiscoveryConfig

The complete API reference is available in ``API.md``.
"""

from __future__ import annotations

from casconf.api import merge_configs
from casconf.discovery import DiscoveryConfig
from casconf.exceptions import (
    CasConfConfigError,
    CasConfError,
    CasConfMergeError,
    CasConfParseError,
    CasConfWriteError,
)

__all__ = [
    "merge_configs",
    "DiscoveryConfig",
    "CasConfError",
    "CasConfConfigError",
    "CasConfParseError",
    "CasConfMergeError",
    "CasConfWriteError",
]
