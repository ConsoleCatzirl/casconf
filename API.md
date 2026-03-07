# CascConf API Reference

This document describes the public Python library API for CascConf.

## Installation

```bash
pip install cascconf
```

## Quick Start

```python
from cascconf import merge_configs

# Merge configurations and return as a dict
config = merge_configs(discovery_config='./cascconf.yaml')
print(config['database']['host'])

# Merge configurations and write to a file
merge_configs(
    discovery_config='./cascconf.yaml',
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
    discovery_config: str | Path | DiscoveryConfig = 'cascconf.yaml',
    output: str | Path | None = None,
    output_format: str = 'json',
    log_level: int = logging.WARNING,
) -> dict[str, Any] | None:
    ...
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `discovery_config` | `str`, `Path`, or `DiscoveryConfig` | `'cascconf.yaml'` | Path to the discovery configuration file, or a `DiscoveryConfig` object. |
| `output` | `str`, `Path`, or `None` | `None` | Path to the output file. If `None`, returns the merged dict. |
| `output_format` | `str` | `'json'` | Output format when writing to a file. One of `'json'`, `'yaml'`, `'toml'`. |
| `log_level` | `int` | `logging.WARNING` | Logging level for merge operations. Use `logging.DEBUG` for verbose output. |

#### Returns

- `dict[str, Any]`: The merged configuration, if `output` is `None`.
- `None`: If `output` is specified (the result is written to the file).

#### Raises

- `CascConfConfigError`: If the discovery configuration is invalid.
- `CascConfParseError`: If a configuration file cannot be parsed.
- `CascConfMergeError`: If configurations cannot be merged.
- `CascConfWriteError`: If the output file cannot be written.

#### Examples

```python
from cascconf import merge_configs

# Return merged config as a dict
config = merge_configs()

# Use a custom discovery config path
config = merge_configs(discovery_config='/etc/myapp/cascconf.yaml')

# Use a DiscoveryConfig object
from cascconf import DiscoveryConfig
discovery = DiscoveryConfig(
    directories=['/etc/myapp', '~/.config/myapp', './config'],
    patterns=['config.json'],
)
config = merge_configs(discovery_config=discovery)

# Write to a JSON file
merge_configs(
    discovery_config='./cascconf.yaml',
    output='./merged.json',
)

# Write to a YAML file
merge_configs(
    discovery_config='./cascconf.yaml',
    output='./merged.yaml',
    output_format='yaml',
)

# Enable debug logging
import logging
config = merge_configs(log_level=logging.DEBUG)
```

---

### `validate_config()`

Validate a configuration dict against a JSON Schema.

```python
def validate_config(
    config: dict[str, Any],
    schema: str | Path | dict[str, Any],
) -> None:
    ...
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `dict[str, Any]` | The configuration dict to validate. |
| `schema` | `str`, `Path`, or `dict` | Path to a JSON Schema file, or a schema dict. |

#### Returns

`None` — raises on validation failure.

#### Raises

- `CascConfValidationError`: If the configuration does not match the schema.

#### Example

```python
from cascconf import merge_configs, validate_config
from cascconf.exceptions import CascConfValidationError

config = merge_configs(discovery_config='./cascconf.yaml')

try:
    validate_config(config, schema='./schema.json')
except CascConfValidationError as e:
    print(f"Invalid config: {e}")
```

---

### `DiscoveryConfig`

Configuration object for the CascConf discovery engine.

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
discovery = DiscoveryConfig.from_file('./cascconf.yaml')
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
from cascconf import DiscoveryConfig, merge_configs

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

All CascConf exceptions are importable from `cascconf.exceptions`.

```python
from cascconf.exceptions import (
    CascConfError,
    CascConfConfigError,
    CascConfParseError,
    CascConfMergeError,
    CascConfWriteError,
    CascConfValidationError,
)
```

### Exception Hierarchy

```
CascConfError (base)
├── CascConfConfigError     — Invalid discovery configuration
├── CascConfParseError      — Failed to parse a configuration file
├── CascConfMergeError      — Irreconcilable merge conflict
├── CascConfWriteError      — Failed to write output
└── CascConfValidationError — Configuration failed schema validation
```

### `CascConfError`

Base class for all CascConf exceptions.

```python
class CascConfError(Exception):
    """Base exception for all CascConf errors."""
```

### `CascConfConfigError`

Raised when the discovery configuration is invalid (missing required keys, invalid values, unreadable file).

```python
class CascConfConfigError(CascConfError):
    """Raised when the discovery configuration is invalid."""
```

### `CascConfParseError`

Raised when a configuration file cannot be read or parsed.

```python
class CascConfParseError(CascConfError):
    """Raised when a configuration file cannot be parsed.

    Attributes:
        path: The path to the file that failed to parse.
    """
    path: Path
```

### `CascConfMergeError`

Raised when configurations cannot be merged due to an irreconcilable conflict.

```python
class CascConfMergeError(CascConfError):
    """Raised when configurations cannot be merged."""
```

### `CascConfWriteError`

Raised when the output file cannot be written (permission denied, invalid path, unsupported format).

```python
class CascConfWriteError(CascConfError):
    """Raised when the output cannot be written."""
```

### `CascConfValidationError`

Raised when the merged configuration does not match the provided schema.

```python
class CascConfValidationError(CascConfError):
    """Raised when the configuration fails schema validation.

    Attributes:
        errors: List of validation error messages.
    """
    errors: list[str]
```

---

## Usage Examples

### Handling Errors Gracefully

```python
from cascconf import merge_configs
from cascconf.exceptions import CascConfError, CascConfParseError

try:
    config = merge_configs(discovery_config='./cascconf.yaml')
except CascConfParseError as e:
    print(f"Could not parse {e.path}: {e}")
    raise SystemExit(1)
except CascConfError as e:
    print(f"CascConf error: {e}")
    raise SystemExit(1)
```

### Application Configuration Loader

```python
import logging
from functools import lru_cache
from cascconf import merge_configs, DiscoveryConfig
from cascconf.exceptions import CascConfError

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
    except CascConfError as e:
        logger.critical("Failed to load configuration: %s", e)
        raise
```

### Multi-Environment Configuration

```python
import os
from cascconf import DiscoveryConfig, merge_configs

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
| `CASCCONF_DISCOVERY` | Default path to the discovery configuration file | `cascconf.yaml` |
| `CASCCONF_LOG_LEVEL` | Default log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `WARNING` |

```python
import os
os.environ['CASCCONF_DISCOVERY'] = '/etc/myapp/cascconf.yaml'

from cascconf import merge_configs
config = merge_configs()  # Uses /etc/myapp/cascconf.yaml
```

---

## Type Hints

CascConf ships with a `py.typed` marker (PEP 561). Full type hints are available for all public API functions and classes. Type checkers such as `mypy` and `pyright` are fully supported.

```python
from typing import Any
from cascconf import merge_configs, DiscoveryConfig

def load(discovery: DiscoveryConfig) -> dict[str, Any]:
    result = merge_configs(discovery_config=discovery)
    assert result is not None  # output=None returns a dict
    return result
```

---

## Logging

CascConf uses the standard `logging` module under the logger name `cascconf`. To see detailed merge information, configure logging before calling `merge_configs()`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from cascconf import merge_configs
config = merge_configs()
```

Or pass `log_level` directly:

```python
from cascconf import merge_configs
config = merge_configs(log_level=logging.DEBUG)
```

Log levels:
- `DEBUG`: Shows each file discovered, parsed, and merged.
- `INFO`: Shows summary counts (files found, merged).
- `WARNING`: Shows warnings (missing directories, type conflicts).
- `ERROR`: Shows errors only (see also exceptions).

---

## Thread Safety

`merge_configs()` and `validate_config()` are **thread-safe** as long as the underlying configuration files are not modified during the call. `DiscoveryConfig` objects are immutable after construction and safe to share across threads.
