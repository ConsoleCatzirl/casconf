# CasConf Design Document

This document explains the key design decisions made for CasConf, including the rationale behind each choice and the trade-offs considered.

## Design Goals

1. **Correctness**: Produce a predictable, reproducible merged configuration.
2. **Simplicity**: Easy to understand, configure, and use correctly.
3. **Composability**: Work well with other Unix tools.
4. **Extensibility**: Support new formats without core changes.
5. **Transparency**: Make the merge process visible (verbose mode, clear errors).

## Non-Goals

- Secret management or encryption.
- Configuration deployment or distribution.
- Support for binary configuration formats.

---

## Key Design Decisions

### 1. Cascading Order: Explicit Discovery Configuration

**Decision**: The order in which directories are scanned is defined explicitly in a discovery configuration file (`casconf.yaml`), not inferred from the environment or hard-coded.

**Rationale**: Implicit discovery orders (e.g., "always check `/etc` first, then `~/.config`, then `.`") are convenient for simple cases but become brittle when applications have non-standard directory layouts. An explicit discovery configuration is:
- Reproducible: the same config produces the same merge result everywhere.
- Transparent: the cascade order is visible in version control.
- Flexible: supports arbitrary directory hierarchies.

**Trade-off**: Users must write a discovery configuration file. This is a small cost for a significant gain in reliability.

---

### 2. Deep Merge by Default

**Decision**: Nested dictionaries are recursively merged (deep merge) by default. Shallow merge is available as an opt-in strategy.

**Rationale**: The primary use case is layered configuration (e.g., defaults → environment-specific overrides). With shallow merge, an override file that touches only one nested key must duplicate the entire parent object. Deep merge allows fine-grained overrides with minimal repetition.

**Trade-off**: Deep merge can produce surprising results when a later config is intended to completely replace a nested object. Users who need replace semantics can use a special key prefix (planned for a future release) or switch to shallow merge.

---

### 3. List Merge Strategy: Append

**Decision**: When both configs contain a list at the same key, the lists are concatenated (later list appended to earlier list).

**Rationale**: Lists in configuration files typically represent collections of items (e.g., allowed hosts, plugin names, search paths). Appending preserves all items from all levels of the cascade, which is the most common desired behavior.

**Trade-off**: If a later config intends to replace a list entirely, concatenation produces incorrect results. A future release will support a `!replace` list merge directive. For now, users who need list replacement can use shallow merge or restructure their configuration.

---

### 4. Format Detection: Extension-Based with Fallback

**Decision**: File format is detected from the file extension. If the extension is unknown or absent, CasConf attempts each known parser in order until one succeeds.

**Rationale**: Extension-based detection is fast, predictable, and consistent with how most tools work. The fallback parser chain handles edge cases (files without extensions, non-standard extensions) without requiring user intervention.

**Trade-off**: A file with an incorrect extension will be parsed by the wrong parser, producing a confusing error. Users are encouraged to use standard extensions.

---

### 5. Dual Interface: CLI + Library

**Decision**: CasConf is both a command-line tool and an importable Python library with a clean public API.

**Rationale**: Configuration management is needed in two contexts:
- **Build and deployment scripts**: the CLI is simpler and avoids Python import overhead.
- **Application startup**: the library allows reading merged configuration directly into the application without spawning a subprocess.

Both interfaces use the same underlying engines, ensuring consistent behavior.

**Trade-off**: Maintaining two interfaces adds some complexity. The library interface is a thin wrapper over the CLI engines, minimizing duplication.

---

### 6. Output Behavior: stdout by Default

**Decision**: The CLI writes to stdout by default. The `--output` flag writes to a file. There is no `--dry-run` flag.

**Rationale**: Defaulting to stdout follows the Unix Philosophy and eliminates the need for a `--dry-run` flag. If a user wants to preview the merged configuration without writing to a file, they simply run `casconf` without `--output`. This is simpler, more composable, and consistent with Unix tools like `cat`, `jq`, and `grep`.

**Implication**: The absence of a `--dry-run` flag is intentional. stdout *is* the dry run.

**Trade-off**: Users accustomed to tools that default to writing files may be surprised. The documentation is clear about this behavior.

---

### 7. Error Handling: Fail Fast vs Continue

**Decision**: CasConf fails fast on errors by default. There is no `--ignore-errors` flag in v1.

**Rationale**: Silent failures in configuration management are dangerous. If a file cannot be read or parsed, it is better to stop immediately with a clear error than to produce a silently incomplete merged configuration. Missing directories are treated as warnings (not errors) because it is common for some directories in a cascade to not exist on all machines.

**Trade-off**: Strict error handling may be inconvenient in some CI environments where certain config files are optional. A `--allow-missing` or `--optional-patterns` feature is planned for a future release.

---

### 8. Discovery Configuration Location

**Decision**: By default, CasConf looks for `casconf.yaml` in the current working directory. The `--discovery-config` flag overrides this.

**Rationale**: Placing the discovery config in the project directory is consistent with how other tools (`.eslintrc`, `pyproject.toml`, etc.) locate their configuration. It makes the cascade definition visible to anyone working in the project.

**Trade-off**: Projects that do not want a `casconf.yaml` in their root directory must always use `--discovery-config`. This is a minor inconvenience.

---

### 9. Directory Glob Support

**Decision**: Directory paths in the discovery configuration support glob patterns (e.g., `./plugins/*/config`).

**Rationale**: Plugin-based applications often have a variable number of plugin directories. Glob support eliminates the need to list each plugin directory explicitly, making the discovery config maintainable as the plugin set grows.

**Trade-off**: Glob expansion happens at merge time, so the set of directories can change between runs. This is usually desirable (new plugins are picked up automatically) but can cause non-determinism if glob order is not predictable. CasConf sorts glob-expanded paths lexicographically.

---

### 10. Metadata Preservation

**Decision**: CasConf does not preserve or expose source file metadata (e.g., which file a particular value came from) in the merged output.

**Rationale**: The output is a plain configuration dict/file. Embedding metadata would require a non-standard output format and complicate downstream consumption. Verbose mode (`--verbose`) provides file-level provenance during the merge run.

**Trade-off**: Users cannot determine the source of a value from the merged output alone. Verbose mode and source tracking (planned for a future release) address this.

---

### 11. File Format Support

**Decision**: Support JSON, YAML, TOML, and INI formats. XML is not supported.

**Rationale**:
- **JSON**: Universal, strict, machine-friendly.
- **YAML**: Human-friendly, widely used for configuration.
- **TOML**: Growing adoption for Python projects (`pyproject.toml`).
- **INI**: Legacy support for existing applications.
- **XML**: Not a configuration format in modern practice; adds significant complexity.

**Trade-off**: Some legacy systems use XML for configuration. Users with XML configuration files must convert them or pre-process them with another tool before using CasConf.

---

### 12. Cross-Format Merging

**Decision**: CasConf can merge configuration files in different formats within the same cascade (e.g., a JSON file and a YAML override file).

**Rationale**: The internal representation is always a Python dict. Format is only relevant at parse time (input) and serialize time (output). Cross-format merging is a natural consequence of this design and a useful feature for real-world deployments.

**Trade-off**: INI files have a flat key structure and limited data types. Merging an INI file with a JSON file that uses nested dicts may produce unexpected results. Users are advised to use a consistent format within a cascade.

---

## Performance Design

CasConf is a batch tool, not a service. Performance targets are:

- **Startup time**: < 500 ms for typical usage (< 10 files, no remote sources).
- **Merge time**: < 100 ms for configurations up to 1 MB total.
- **Memory**: < 50 MB resident for configurations up to 10 MB total.

These targets are met by the simple in-memory merge algorithm. No caching or indexing is needed.

---

## Security Considerations

- **Path traversal**: Directory paths are resolved to absolute paths before use. Paths outside the filesystem root are rejected.
- **Symlink following**: Symlinks in configuration directories are followed by default. This is the standard behavior and allows flexible directory layouts.
- **No code execution**: CasConf never executes code from configuration files. YAML's `yaml.safe_load` is used (not `yaml.load`).

---

## Future Considerations

- **Replace directive**: A `!replace` YAML tag or `__replace: true` key to indicate that a list or dict should replace (not merge) the value from the previous level.
- **Merge exclusions**: A way to specify keys that should not be merged (e.g., secrets injected at runtime).
- **Source tracking**: Annotate the merged output with source file provenance for debugging.
- **Schema validation**: Built-in JSON Schema validation with per-key error messages.
