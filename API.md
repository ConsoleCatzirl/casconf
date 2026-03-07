# CasConf API Reference

This document describes the public Python library API for CasConf.

## Installation

```bash
pip install casconf
```

## Quick Start

```python
from casconf import merge_configs

# Merge configurations and return as a dict
config = merge_configs(discovery_config='./casconf.yaml')
print(config['database']['host'])

# Merge configurations and write to a file
merge_configs(
    discovery_config='./casconf.yaml',
    output='./merged.json',
    output_format='json',
)
```

---

## Public API

### `merge_configs()`

Discover, parse, and deep-merge configuration files.

```python
def merge_configs(
    discovery_config: str | Path | DiscoveryConfig = 'casconf.yaml',
    output: str | Path | None = None,
    output_format: str = 'json',
    log_level: int = logging.WARNING,
) -> dict[str, Any] | None:
    ...
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `discovery_config` | `str`, `Path`, or `DiscoveryConfig` | `'casconf.yaml'` | Path to the discovery configuration file, or a `DiscoveryConfig` object. |
| `output` | `str`, `Path`, or `None` | `None` | Path to the output file. If `None`, returns the merged dict. |
| `output_format` | `str` | `'json'` | Output format when writing to a file. One of `'json'`, `'yaml'`, `'toml'`. |
| `log_level` | `int` | `logging.WARNING` | Logging level for merge operations. Use `logging.DEBUG` for verbose output. |

#### Returns

- `dict[str, Any]`: The merged configuration, if `output` is `None`.
- `None`: If `output` is specified (the result is written to the file).

#### Raises

- `CasConfConfigError`: If the discovery configuration is invalid.
- `CasConfParseError`: If a configuration file cannot be parsed.
- `CasConfMergeError`: If configurations cannot be merged.
- `CasConfWriteError`: If the output file cannot be written.

#### Examples

```python
from casconf import merge_configs

# Return merged config as a dict
config = merge_configs()

# Use a custom discovery config path
config = merge_configs(discovery_config='/etc/myapp/casconf.yaml')

# Use a DiscoveryConfig object
from casconf import DiscoveryConfig
discovery = DiscoveryConfig(
    directories=['/etc/myapp', '~/.config/myapp', './config'],
    patterns=['config.json'],
)
config = merge_configs(discovery_config=discovery)

# Write to a JSON file
merge_configs(
    discovery_config='./casconf.yaml',
    output='./merged.json',
)

# Write to a YAML file
merge_configs(
    discovery_config='./casconf.yaml',
    output='./merged.yaml',
    output_format='yaml',
)

# Enable debug logging
import logging
config = merge_configs(log_level=logging.DEBUG)
```

---

### `DiscoveryConfig`

Configuration object for the CasConf discovery engine.

```python
class DiscoveryConfig:
    def __init__(
        self,
        directories: list[str | Path],
        patterns: list[str],
        merge_strategy: str = 'deep',
    ) -> None:
        ...

    @classmethod
    def from_file(cls, path: str | Path) -> DiscoveryConfig:
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiscoveryConfig:
        ...
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directories` | `list[str \| Path]` | required | Ordered list of directories to scan. Later entries take precedence. Supports `~` expansion and glob patterns. |
| `patterns` | `list[str]` | required | File name patterns to match within each directory. Supports glob wildcards. |
| `merge_strategy` | `str` | `'deep'` | Merge strategy. One of `'deep'` or `'shallow'`. |

#### Class Methods

**`DiscoveryConfig.from_file(path)`**

Load a `DiscoveryConfig` from a YAML, JSON, or TOML file.

```python
discovery = DiscoveryConfig.from_file('./casconf.yaml')
```

**`DiscoveryConfig.from_dict(data)`**

Create a `DiscoveryConfig` from a Python dict.

```python
discovery = DiscoveryConfig.from_dict({
    'directories': ['/etc/myapp', '~/.config/myapp'],
    'patterns': ['config.json'],
    'merge_strategy': 'deep',
})
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `directories` | `list[Path]` | Resolved directory paths. |
| `patterns` | `list[str]` | File name patterns. |
| `merge_strategy` | `str` | Active merge strategy. |

#### Example

```python
from pathlib import Path
from casconf import DiscoveryConfig, merge_configs

discovery = DiscoveryConfig(
    directories=[
        '/etc/myapp',
        Path.home() / '.config' / 'myapp',
        './config',
    ],
    patterns=['config.json', 'config.yaml', '*.conf.json'],
    merge_strategy='deep',
)

config = merge_configs(discovery_config=discovery)
```

---

## Exceptions

All CasConf exceptions are importable from `casconf.exceptions`.

```python
from casconf.exceptions import (
    CasConfError,
    CasConfConfigError,
    CasConfParseError,
    CasConfMergeError,
    CasConfWriteError,
)
```

### Exception Hierarchy

```
CasConfError (base)
├── CasConfConfigError     — Invalid discovery configuration
├── CasConfParseError      — Failed to parse a configuration file
├── CasConfMergeError      — Irreconcilable merge conflict
└── CasConfWriteError      — Failed to write output
```

### `CasConfError`

Base class for all CasConf exceptions.

```python
class CasConfError(Exception):
    """Base exception for all CasConf errors."""
```

### `CasConfConfigError`

Raised when the discovery configuration is invalid (missing required keys, invalid values, unreadable file).

```python
class CasConfConfigError(CasConfError):
    """Raised when the discovery configuration is invalid."""
```

### `CasConfParseError`

Raised when a configuration file cannot be read or parsed.

```python
class CasConfParseError(CasConfError):
    """Raised when a configuration file cannot be parsed.

    Attributes:
        path: The path to the file that failed to parse.
    """
    path: Path
```

### `CasConfMergeError`

Raised when configurations cannot be merged due to an irreconcilable conflict.

```python
class CasConfMergeError(CasConfError):
    """Raised when configurations cannot be merged."""
```

### `CasConfWriteError`

Raised when the output file cannot be written (permission denied, invalid path, unsupported format).

```python
class CasConfWriteError(CasConfError):
    """Raised when the output cannot be written."""
```

---

## Usage Examples

### Handling Errors Gracefully

```python
from casconf import merge_configs
from casconf.exceptions import CasConfError, CasConfParseError

try:
    config = merge_configs(discovery_config='./casconf.yaml')
except CasConfParseError as e:
    print(f"Could not parse {e.path}: {e}")
    raise SystemExit(1)
except CasConfError as e:
    print(f"CasConf error: {e}")
    raise SystemExit(1)
```

### Application Configuration Loader

```python
import logging
from functools import lru_cache
from casconf import merge_configs, DiscoveryConfig
from casconf.exceptions import CasConfError

logger = logging.getLogger(__name__)

_DISCOVERY = DiscoveryConfig(
    directories=[
        '/etc/myapp',
        '~/.config/myapp',
        './config',
    ],
    patterns=['config.json', 'config.yaml'],
)


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load and cache the application configuration."""
    try:
        return merge_configs(
            discovery_config=_DISCOVERY,
            log_level=logging.DEBUG,
        )
    except CasConfError as e:
        logger.critical("Failed to load configuration: %s", e)
        raise
```

### Multi-Environment Configuration

```python
import os
from casconf import DiscoveryConfig, merge_configs

ENV = os.getenv('APP_ENV', 'development')

discovery = DiscoveryConfig(
    directories=[
        '/etc/myapp',
        f'./config/base',
        f'./config/{ENV}',
    ],
    patterns=['config.json'],
)

config = merge_configs(discovery_config=discovery)
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CASCCONF_DISCOVERY` | Default path to the discovery configuration file | `casconf.yaml` |
| `CASCCONF_LOG_LEVEL` | Default log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `WARNING` |

```python
import os
os.environ['CASCCONF_DISCOVERY'] = '/etc/myapp/casconf.yaml'

from casconf import merge_configs
config = merge_configs()  # Uses /etc/myapp/casconf.yaml
```

---

## Type Hints

CasConf ships with a `py.typed` marker (PEP 561). Full type hints are available for all public API functions and classes. Type checkers such as `mypy` and `pyright` are fully supported.

```python
from typing import Any
from casconf import merge_configs, DiscoveryConfig

def load(discovery: DiscoveryConfig) -> dict[str, Any]:
    result = merge_configs(discovery_config=discovery)
    assert result is not None  # output=None returns a dict
    return result
```

---

## Logging

CasConf uses the standard `logging` module under the logger name `casconf`. To see detailed merge information, configure logging before calling `merge_configs()`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from casconf import merge_configs
config = merge_configs()
```

Or pass `log_level` directly:

```python
from casconf import merge_configs
config = merge_configs(log_level=logging.DEBUG)
```

Log levels:
- `DEBUG`: Shows each file discovered, parsed, and merged.
- `INFO`: Shows summary counts (files found, merged).
- `WARNING`: Shows warnings (missing directories, type conflicts).
- `ERROR`: Shows errors only (see also exceptions).

---

## Thread Safety

`merge_configs()` is **thread-safe** as long as the underlying configuration files are not modified during the call. `DiscoveryConfig` objects are immutable after construction and safe to share across threads.
