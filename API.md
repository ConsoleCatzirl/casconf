# CascConf API Reference

This document describes the public Python API of the `cascconf` library.

---

## Installation

```bash
pip install cascconf
```

---

## Top-level Functions

### `cascconf.merge`

```python
cascconf.merge(
    sources: str | Path | None = None,
    filename: str | None = None,
    output: str | Path | None = None,
    output_format: str = "yaml",
    verbose: bool = False,
) -> dict
```

Discover, parse, and deep-merge configuration files according to the given sources file.

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sources` | `str \| Path \| None` | `~/.config/cascconf/sources.yaml` | Path to the discovery (sources) file that lists directories to scan. |
| `filename` | `str \| None` | `None` | If provided, only files whose basename matches this value are considered. If `None`, all supported configuration files are merged. |
| `output` | `str \| Path \| None` | `None` | If provided, the merged result is serialized and written to this file path. If `None`, the result is returned only and no file is written. |
| `output_format` | `str` | `"yaml"` | Serialization format for the written output file. One of `"yaml"`, `"json"`, `"toml"`. Ignored when `output` is `None`. |
| `verbose` | `bool` | `False` | If `True`, emits informational messages (e.g., skipped directories) to stderr. |

#### Returns

A `dict` containing the fully merged configuration data.

#### Raises

| Exception | When |
|---|---|
| `CascConfSourcesNotFoundError` | The sources file does not exist. |
| `CascConfParseError` | A discovered configuration file cannot be parsed. |
| `CascConfOutputError` | The output file cannot be written (e.g., parent directory missing). |

#### Example

```python
import cascconf

# Merge using the default sources file; return the result
config = cascconf.merge()

# Use a custom sources file and restrict to a single filename
config = cascconf.merge(
    sources="/etc/myapp/cascconf-sources.yaml",
    filename="app.yaml",
)

# Write the merged result to disk in JSON format
config = cascconf.merge(output="/etc/myapp/merged.json", output_format="json")
```

---

### `cascconf.load_sources`

```python
cascconf.load_sources(path: str | Path) -> list[Path]
```

Parse a discovery file and return the ordered list of source directories.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str \| Path` | Path to the sources file. |

#### Returns

An ordered `list` of `pathlib.Path` objects representing the directories to scan. Non-existent directories are included as-is; filtering is left to the caller.

#### Raises

| Exception | When |
|---|---|
| `CascConfSourcesNotFoundError` | The sources file does not exist. |
| `CascConfParseError` | The sources file cannot be parsed or is missing the `directories` key. |

---

### `cascconf.discover`

```python
cascconf.discover(
    directories: list[str | Path],
    filename: str | None = None,
) -> list[Path]
```

Walk an ordered list of directories and return matching configuration file paths.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `directories` | `list[str \| Path]` | Ordered list of directories to scan. |
| `filename` | `str \| None` | If provided, only files whose basename matches are returned. |

#### Returns

An ordered `list` of `pathlib.Path` objects for each discovered configuration file, in directory-list order.

---

### `cascconf.parse`

```python
cascconf.parse(path: str | Path) -> dict
```

Parse a single configuration file and return its contents as a `dict`.

Supported formats are determined by file extension: `.yaml`, `.yml`, `.json`, `.toml`.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str \| Path` | Path to the configuration file. |

#### Returns

A `dict` representing the parsed configuration.

#### Raises

| Exception | When |
|---|---|
| `CascConfParseError` | The file cannot be parsed (unsupported extension, syntax error, etc.). |

---

### `cascconf.deep_merge`

```python
cascconf.deep_merge(base: dict, overlay: dict) -> dict
```

Deep-merge two dicts. When the same key exists in both and both values are dicts, they are merged recursively. Otherwise the overlay value takes precedence.

This function is a **pure function** — neither `base` nor `overlay` is modified.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `base` | `dict` | The lower-priority dict. |
| `overlay` | `dict` | The higher-priority dict whose values win on conflict. |

#### Returns

A new `dict` representing the merged result.

#### Example

```python
from cascconf import deep_merge

base    = {"a": 1, "b": {"x": 10, "y": 20}}
overlay = {"b": {"y": 99, "z": 30}, "c": 3}

result = deep_merge(base, overlay)
# {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3}
```

---

### `cascconf.register_parser`

```python
cascconf.register_parser(extension: str, parser: Callable[[Path], dict]) -> None
```

Register a custom file parser for a given file extension.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `extension` | `str` | File extension including the leading dot (e.g., `".ini"`). |
| `parser` | `Callable[[Path], dict]` | A callable that accepts a `pathlib.Path` and returns a `dict`. |

#### Example

```python
import configparser
import cascconf

def parse_ini(path):
    cp = configparser.ConfigParser()
    cp.read(path)
    return {s: dict(cp[s]) for s in cp.sections()}

cascconf.register_parser(".ini", parse_ini)

config = cascconf.merge(filename="settings.ini")
```

---

## Exceptions

### `cascconf.CascConfError`

Base class for all CascConf exceptions.

---

### `cascconf.CascConfSourcesNotFoundError`

Raised when the sources file cannot be found.

```
cascconf.CascConfSourcesNotFoundError: Sources file not found: /path/to/sources.yaml
```

---

### `cascconf.CascConfParseError`

Raised when a configuration file (or the sources file) cannot be parsed.

```
cascconf.CascConfParseError: Failed to parse /etc/myapp/config.yaml: ...
```

---

### `cascconf.CascConfOutputError`

Raised when the merged result cannot be written to the specified output path.

```
cascconf.CascConfOutputError: Cannot write output to /nonexistent/dir/result.yaml: ...
```

---

## Type Aliases

```python
from cascconf.types import MergedConfig  # alias for dict[str, Any]
```

---

## Compatibility

| Python version | Supported |
|---|---|
| 3.9 | ✅ |
| 3.10 | ✅ |
| 3.11 | ✅ |
| 3.12 | ✅ |
| 3.13 | ✅ |
