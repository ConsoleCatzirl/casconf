# CasConf Architecture

This document describes the system design and component overview for CasConf.

## Design Principles

CasConf is built on the following principles:

### Unix Philosophy
Do one thing and do it well. CasConf merges configuration files. It does not deploy applications, manage secrets, or validate business logic. It outputs to stdout by default, enabling composition with other tools.

### Separation of Concerns
Each component has a single, well-defined responsibility:
- **Discovery**: find configuration files
- **Parsing**: read and decode file content
- **Merging**: combine configurations
- **Writing**: output the result

### Extensibility
New file formats, merge strategies, and output formats can be added without modifying existing components.

### Minimal Dependencies
CasConf avoids unnecessary third-party dependencies. The standard library covers most needs; optional dependencies are used only for non-standard formats (e.g., TOML, YAML).

### PEP 8 Compliance
All Python code follows PEP 8 style guidelines. Code is readable, consistently formatted, and easy to maintain.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CasConf                                │
│                                                                 │
│  Input: Discovery Configuration (file or programmatic object)  │
│                                                                 │
│  ┌──────────────────┐                                           │
│  │  Discovery Engine │  Scans directories for matching files   │
│  └────────┬─────────┘                                           │
│           │  [list of file paths, ordered by priority]          │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │   Parser Engine  │  Reads and decodes each file             │
│  └────────┬─────────┘                                           │
│           │  [list of parsed configuration dicts]               │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │   Merger Engine  │  Deep-merges configurations in order     │
│  └────────┬─────────┘                                           │
│           │  [single merged configuration dict]                 │
│           ▼                                                     │
│  ┌──────────────────┐                                           │
│  │   Writer Engine  │  Serializes and writes output            │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  Output: stdout (default) or file                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### Discovery Engine

**Responsibility**: Locate configuration files based on a discovery configuration.

**Inputs**:
- A `DiscoveryConfig` object specifying directories, file patterns, and merge strategy.

**Outputs**:
- An ordered list of file paths to merge, from lowest to highest priority.

**Behavior**:
- Iterates over directories in the order they are specified.
- For each directory, checks each pattern in order.
- Skips directories that do not exist or are not readable (with a warning).
- Expands `~` (home directory) and environment variables in directory paths.
- Supports glob patterns in directory paths (e.g., `./plugins/*/config`).

---

### Parser Engine

**Responsibility**: Read and decode a configuration file into a Python dictionary.

**Inputs**:
- A file path.

**Outputs**:
- A Python `dict` representing the parsed configuration.

**Behavior**:
- Detects file format from the file extension (`.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`).
- Falls back to attempting each known parser if extension detection fails.
- Raises `CasConfParseError` with a descriptive message on parse failure.
- Returns an empty dict for empty files (not an error).

**Supported Formats**:
- JSON (built-in `json` module)
- YAML (requires `pyyaml`)
- TOML (requires `tomllib` on Python 3.11+, or `tomli`)
- INI/CFG (built-in `configparser` module)

---

### Merger Engine

**Responsibility**: Combine multiple configuration dictionaries into one.

**Inputs**:
- An ordered list of Python dicts (from lowest to highest priority).
- A merge strategy (`deep` or `shallow`).

**Outputs**:
- A single Python dict representing the merged configuration.

**Behavior (Deep Merge)**:
- Scalars (strings, numbers, booleans, null): later value replaces earlier value.
- Dicts: recursively merged key by key.
- Lists: later list is appended to earlier list (concatenation).
- Type conflicts (e.g., a scalar in one file and a dict in another): later type wins, with a warning.

**Behavior (Shallow Merge)**:
- Top-level keys from later dicts replace top-level keys from earlier dicts entirely (no recursion).

---

### Writer Engine

**Responsibility**: Serialize the merged configuration and write it to the output destination.

**Inputs**:
- A Python dict (the merged configuration).
- An output format (`json`, `yaml`, `toml`).
- An output destination (file path or stdout).

**Outputs**:
- Serialized configuration written to the destination.

**Behavior**:
- Defaults to JSON format.
- Writes to stdout if no output path is provided.
- Creates parent directories if writing to a file and they do not exist.
- Uses human-friendly formatting (indentation, sorted keys for JSON).

---

### Configuration Registry

**Responsibility**: Map file extensions to parser implementations and manage format aliases.

**Behavior**:
- Maintains a mapping of extensions → parser callables.
- Allows registration of custom parsers at runtime.
- Used by both the Parser Engine and the Writer Engine.

---

## Data Flow

### CLI Usage

```
User
  │
  │  casconf --discovery-config ./casconf.yaml --output ./merged.json
  ▼
CLI Entry Point (casconf/__main__.py)
  │
  │  Parses CLI arguments
  │  Loads discovery config from file
  ▼
DiscoveryConfig object
  │
  ▼
Discovery Engine → [file1, file2, file3]
  │
  ▼
Parser Engine → [dict1, dict2, dict3]
  │
  ▼
Merger Engine → merged_dict
  │
  ▼
Writer Engine → ./merged.json (or stdout)
```

### Library Usage

```python
from casconf import merge_configs

config = merge_configs(discovery_config='./casconf.yaml')
```

```
Python Application
  │
  │  merge_configs(discovery_config='./casconf.yaml')
  ▼
Public API (casconf/__init__.py)
  │
  │  Accepts file path or DiscoveryConfig object
  ▼
DiscoveryConfig object
  │
  ▼
Discovery Engine → [file1, file2, file3]
  │
  ▼
Parser Engine → [dict1, dict2, dict3]
  │
  ▼
Merger Engine → merged_dict
  │
  │  Returns merged_dict to caller
  │  (or writes to file if output= is specified)
  ▼
Python dict (or file on disk)
```

---

## Module Structure

```
casconf/
├── __init__.py          # Public API: merge_configs(), validate_config(), DiscoveryConfig
├── __main__.py          # CLI entry point
├── cli.py               # CLI argument parsing and orchestration
├── discovery.py         # Discovery Engine: DiscoveryConfig, file scanning
├── parser.py            # Parser Engine: format detection, file parsing
├── merger.py            # Merger Engine: deep/shallow merge logic
├── writer.py            # Writer Engine: serialization, output routing
├── registry.py          # Configuration Registry: format → parser/writer mapping
├── exceptions.py        # Exception hierarchy
└── py.typed             # PEP 561 marker for type checking
```

---

## Key Design Patterns

### Strategy Pattern
The merge strategy (`deep` vs `shallow`) and output format (`json`, `yaml`, `toml`) are implemented as interchangeable strategies. The Merger Engine and Writer Engine accept a strategy parameter and delegate to the appropriate implementation.

### Factory Pattern
The Parser Engine uses a factory to instantiate the correct parser for a given file extension. The Configuration Registry acts as the factory registry.

### Registry Pattern
The Configuration Registry maps format identifiers to parser and writer callables. Custom formats can be registered at runtime, enabling extensibility without modifying core code.

### Chain of Responsibility
Configuration files are processed in a chain: each file's parsed dict is passed to the merger along with the accumulated result from all previous files. This produces the final merged configuration.

---

## Error Handling

### Exception Types

| Exception | Description |
|-----------|-------------|
| `CasConfError` | Base exception for all CasConf errors |
| `CasConfConfigError` | Invalid discovery configuration |
| `CasConfParseError` | Failed to parse a configuration file |
| `CasConfMergeError` | Irreconcilable merge conflict |
| `CasConfWriteError` | Failed to write output |
| `CasConfValidationError` | Configuration failed schema validation |

### Strategy
- **Fail fast on configuration errors**: A malformed discovery config raises immediately.
- **Fail fast on parse errors**: An unreadable or unparseable file raises immediately (no silent data loss).
- **Warn on non-fatal issues**: Missing directories and type conflicts emit warnings but do not raise.
- **No silent failures**: Every error path produces a message that identifies the problematic file or setting.

---

## Performance Considerations

- Files are read once and not cached (configuration merging is not a hot path).
- The merge algorithm is O(n × d) where n is the number of files and d is the depth of nesting.
- Large configuration files (megabytes) are supported but not optimized for.
- The tool is not designed for real-time or high-frequency invocation (use environment variables for that).

---

## Testing Strategy

- **Unit tests** for each engine component in isolation.
- **Integration tests** for end-to-end CLI and library usage.
- **Fixture-based tests** using sample configuration files in `tests/fixtures/`.
- **Property-based tests** for the merge algorithm (using `hypothesis`).

---

## Dependencies

### Required
- Python 3.9+
- `pyyaml` — YAML parsing and serialization

### Optional
- `tomli` — TOML parsing on Python < 3.11 (Python 3.11+ includes `tomllib`)
- `tomli-w` — TOML serialization

### Development
- `pytest` — Test runner
- `pytest-cov` — Coverage reporting
- `hypothesis` — Property-based testing
- `mypy` — Static type checking
- `ruff` — Linting and formatting

---

## Future Extensibility

The following capabilities are planned or considered for future releases:

- **Custom merge strategies**: Allow users to define per-key merge behavior.
- **Remote sources**: Fetch configuration files from HTTP URLs or object storage.
- **Secret injection**: Resolve secret references (e.g., `${SECRET:my-secret}`) at merge time.
- **Schema validation**: Built-in JSON Schema validation for the merged output.
- **Watch mode**: Re-merge and re-output when source files change.
- **Custom parsers**: Allow registration of user-defined parsers for non-standard formats.
