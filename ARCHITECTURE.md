# CascConf Architecture

## Overview

CascConf is structured as a thin CLI wrapper around a reusable Python library. The library performs all core logic; the CLI is responsible only for parsing arguments and wiring input/output streams.

```
┌──────────────────────────────────────────────────────┐
│                    User / Shell                      │
└──────────┬───────────────────────────┬───────────────┘
           │ CLI invocation            │ Library import
           ▼                           ▼
┌──────────────────┐       ┌──────────────────────────┐
│   CLI Layer      │       │  Library API (cascconf)   │
│  (cascconf cmd)  │──────▶│  merge(), load(), etc.    │
└──────────────────┘       └────────────┬─────────────┘
                                        │
                    ┌───────────────────▼──────────────┐
                    │         Core Pipeline             │
                    │  1. Source Loader                 │
                    │  2. File Discoverer               │
                    │  3. File Parser                   │
                    │  4. Deep Merger                   │
                    │  5. Output Serializer             │
                    └──────────────────────────────────┘
```

---

## Components

### 1. Source Loader

**Responsibility:** Read the *discovery file* (also called the *sources file*) and return an ordered list of directories to scan.

- Reads a YAML, JSON, or TOML file whose `directories` key contains an ordered list of directory paths.
- Expands `~` home-directory references and environment variables in paths.
- Validates that all listed paths are strings; non-existent directories are silently skipped (with an optional warning in verbose mode).

**Default discovery file location:** `~/.config/cascconf/sources.yaml`

### 2. File Discoverer

**Responsibility:** Walk each source directory and collect configuration file paths, in directory-list order.

- For each directory in the ordered list, scans the top level (non-recursive by default) for files with supported extensions: `.yaml`, `.yml`, `.json`, `.toml`.
- When a `--file` / `filename` filter is provided, only files whose basename matches the filter are collected.
- Returns an ordered list of `(directory, filepath)` tuples, preserving the priority order.

### 3. File Parser

**Responsibility:** Deserialize each discovered configuration file into a Python `dict`.

- Delegates to the appropriate parser based on file extension:
  - `.yaml` / `.yml` → [PyYAML](https://pyyaml.org/) (`yaml.safe_load`)
  - `.json` → standard library `json`
  - `.toml` → [tomllib](https://docs.python.org/3/library/tomllib.html) (stdlib ≥ 3.11) or [tomli](https://github.com/hukkin/tomli) (backport)
- Parse errors surface as a `CascConfParseError` with the offending file path included in the message.

### 4. Deep Merger

**Responsibility:** Combine an ordered sequence of dicts into a single dict using deep-merge semantics.

Deep-merge rules:
- If a key exists in both the *base* and the *overlay* and **both values are dicts**, recurse.
- Otherwise the **overlay value wins** (later source takes precedence).
- Lists are replaced, not concatenated (consistent, predictable behavior).

The merger is a pure function with no side effects, making it easy to test in isolation and to use in library mode.

### 5. Output Serializer

**Responsibility:** Convert the merged `dict` back into a text representation.

- Supported output formats: `yaml` (default), `json`, `toml`.
- In CLI mode, writes to the path specified by `--output`, or stdout if no path is given.
- In library mode, writes to file only when an `output` path is explicitly provided by the caller; otherwise returns the `dict` directly.

---

## Data Flow

```
sources.yaml
     │
     ▼
[Source Loader] ──► ordered list of directories
                            │
                            ▼
              [File Discoverer] ──► ordered list of file paths
                                            │
                                            ▼
                              [File Parser] ──► list of dicts
                                                     │
                                                     ▼
                                   [Deep Merger] ──► merged dict
                                                          │
                                    ┌─────────────────────┘
                                    ▼
                       [Output Serializer] ──► stdout / file
```

---

## Design Decisions

### Unix Philosophy

CascConf is intentionally minimal:

- **One job:** merge configuration files.
- **Text in, text out:** all I/O uses human-readable text formats.
- **Composable:** because output defaults to stdout, CascConf pipelines naturally with `envsubst`, `jq`, `yq`, deployment tools, and other utilities.

### No implicit side effects in library mode

When CascConf is imported as a library, it never writes to disk unless the caller explicitly passes an `output` path. This avoids surprising behavior when CascConf is embedded in larger applications.

### Format agnosticism

Users may store different layers of their configuration in different formats (e.g., a base layer in TOML, an override layer in YAML). CascConf normalises every file into a Python `dict` before merging, so formats can be mixed freely within a single merge operation.

### Ordered precedence

Directory order is explicit and user-controlled via the sources file. There is no implicit search-path magic; what you configure is exactly what runs. This makes behavior reproducible and auditable.

---

## Error Handling

| Situation | Behavior |
|---|---|
| Sources file not found | Fatal error with helpful message |
| Source directory does not exist | Warning (verbose mode); directory skipped |
| Config file cannot be parsed | Fatal `CascConfParseError` identifying the file |
| Output file directory does not exist | Fatal error with path included |
| No configuration files discovered | Empty dict returned / empty document written |

---

## Extension Points

- **Custom parsers** — additional file-format parsers can be registered via `cascconf.register_parser(extension, callable)`.
- **Custom merge strategies** — the default deep-merger can be replaced or extended by passing a `merger` callable to `cascconf.merge()`.

---

## Future Considerations

- Recursive directory scanning (opt-in flag `--recursive`).
- Schema validation of the merged result.
- Watch mode for live reloading on file changes.
- Plugin system for secret backends (e.g., Vault, AWS SSM).
