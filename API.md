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
    merge_strategy: str = "deep",
    list_merge: str = "replace",
    verbose: bool = False,
) -> dict
```

Discover, parse, and deep-merge configuration files according to the given sources file.

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sources` | `str \| Path \| None` | `~/.config/cascconf/sources.yaml` | Path to the discovery (sources) file that lists directories to scan. |
| `filename` | `str \| None` | `None` | If provided, only files whose basename matches this value are considered. If `None`, files matching the patterns in the sources file are merged. |
| `output` | `str \| Path \| None` | `None` | If provided, the merged result is serialized and written to this file path. If `None`, the result is returned only and no file is written. |
| `output_format` | `str` | `"yaml"` | Serialization format for the written output file. One of `"yaml"`, `"json"`, `"toml"`, `"ini"`. Ignored when `output` is `None`. |
| `merge_strategy` | `str` | `"deep"` | How to merge nested structures. One of `"deep"` (recursive) or `"shallow"` (top-level only). |
| `list_merge` | `str` | `"replace"` | How to merge list values. One of `"replace"`, "append", or "union". |
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

# Use append strategy for lists
config = cascconf.merge(
    sources="/etc/myapp/sources.yaml",
    merge_strategy="deep",
    list_merge="append"
)
```

---

### `cascconf.load_sources`

```python
cascconf.load_sources(path: str | Path) -> dict
```

Parse a discovery file and return the full configuration.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `path` | `str \| Path` | Path to the sources file. |

#### Returns

A `dict` containing:
- `directories`: Ordered list of `pathlib.Path` objects representing the directories to scan.
- `patterns`: List of glob patterns for file matching.
- `merge_strategy`: The configured merge strategy.
- `list_merge`: The configured list merge strategy.

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
    patterns: list[str] | None = None,
    filename: str | None = None,
) -> list[Path]
```

Walk an ordered list of directories and return matching configuration file paths.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `directories` | `list[str \| Path]` | Ordered list of directories to scan. |
| `patterns` | `list[str] \| None` | Glob patterns for matching files. If `None`, matches all supported extensions. |
| `filename` | `str \| None` | If provided, only files whose basename matches are returned. |

#### Returns

An ordered `list` of `pathlib.Path` objects for each discovered configuration file, in directory-list order.

---

### `cascconf.parse`

```python
cascconf.parse(path: str | Path) -> dict
```

Parse a single configuration file and return its contents as a `dict`.

Supported formats are determined by file extension: `.yaml`, `.yml`, `.json`, `.toml`, `.ini`, `.cfg`.

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
cascconf.deep_merge(
    base: dict,
    overlay: dict,
    list_merge: str = "replace"
) -> dict
```

Deep-merge two dicts. When the same key exists in both and both values are dicts, they are merged recursively. Otherwise the overlay value takes precedence.

This function is a **pure function** — neither `base` nor `overlay` is modified.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| `base` | `dict` | The lower-priority dict. |
| `overlay` | `dict` | The higher-priority dict whose values win on conflict. |
| `list_merge` | `str` | How to merge lists: `"replace"`, `"append"`, or `"union"`. |

#### Returns

A new `dict` representing the merged result.

#### Example

```python
from cascconf import deep_merge

base    = {"a": 1, "b": {"x": 10, "y": 20}, "items": [1, 2]}
overlay = {"b": {"y": 99, "z": 30}, "c": 3, "items": [3, 4]}

# With replace (default)
result = deep_merge(base, overlay, list_merge="replace")
# {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3, "items": [3, 4]}

# With append
result = deep_merge(base, overlay, list_merge="append")
# {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3, "items": [1, 2, 3, 4]}

# With union
result = deep_merge(base, overlay, list_merge="union")
# {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3, "items": [1, 2, 3, 4]}
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
import cascconf

def parse_custom(path):
    # Custom parsing logic
    with open(path) as f:
        return {"content": f.read()}

cascconf.register_parser(".custom", parse_custom)

config = cascconf.merge(filename="settings.custom")
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