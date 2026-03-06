# CascConf Quick Start

## Requirements

- Python 3.9 or later
- pip

## Installation

```bash
pip install cascconf
```

To install from source:

```bash
git clone https://github.com/ConsoleCatzirl/cascconf.git
cd cascconf
pip install .
```

## Basic Concepts

CascConf discovers configuration files from an ordered list of directories and **deep-merges** them. A *deep merge* means nested structures are combined key-by-key rather than replaced wholesale. Files discovered later in the directory list take precedence over earlier ones.

### Discovery file

CascConf reads a *discovery file* to know which directories to scan. The default discovery file is `~/.config/cascconf/sources.yaml`, but you can specify a different one with the `--sources` flag.

```yaml
# sources.yaml
directories:
  - /etc/myapp
  - /usr/local/etc/myapp
  - ~/.config/myapp
  - ./config
```

Directories are scanned in the order listed. Files with the same name found in multiple directories are merged, with later entries winning on conflicts.

### Configuration file formats

CascConf supports **YAML** (`.yaml`, `.yml`), **JSON** (`.json`), and **TOML** (`.toml`) configuration files. All discovered files with a supported extension are eligible for merging.

---

## CLI Usage

### Merge all discovered files and print to stdout

```bash
cascconf
```

### Specify a custom discovery (sources) file

```bash
cascconf --sources /path/to/sources.yaml
```

### Write merged output to a file

```bash
cascconf --output /path/to/result.yaml
```

### Select a specific config file name to merge

```bash
cascconf --file app.yaml
```

By default, CascConf merges every supported configuration file it discovers. Use `--file` to restrict merging to files with a specific name.

### Control output format

```bash
cascconf --format json
```

Supported formats: `yaml` (default), `json`, `toml`.

### Verbose/debug output

```bash
cascconf --verbose
```

---

## Example Walkthrough

Given the following `sources.yaml`:

```yaml
directories:
  - /etc/myapp
  - ~/.config/myapp
```

And two files with the same name `settings.yaml`:

**`/etc/myapp/settings.yaml`**
```yaml
database:
  host: localhost
  port: 5432
logging:
  level: INFO
```

**`~/.config/myapp/settings.yaml`**
```yaml
database:
  port: 5433
  name: mydb
```

Running `cascconf --file settings.yaml` produces:

```yaml
database:
  host: localhost   # from /etc/myapp
  port: 5433        # overridden by ~/.config/myapp
  name: mydb        # added by ~/.config/myapp
logging:
  level: INFO       # from /etc/myapp
```

---

## Library Usage

```python
import cascconf

# Merge using the default discovery file
result = cascconf.merge()

# Merge using a custom discovery file
result = cascconf.merge(sources="/path/to/sources.yaml")

# Restrict to a specific filename
result = cascconf.merge(sources="/path/to/sources.yaml", filename="app.yaml")

# Write output to file (opt-in)
result = cascconf.merge(output="/path/to/result.yaml")

# Access merged values
print(result["database"]["host"])
```

See [API.md](API.md) for full library documentation.

---

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand how CascConf works internally.
- Read [API.md](API.md) for the full Python library reference.
- Read [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to contribute.
