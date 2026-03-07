# CasConf Quick Start Guide

This guide walks you through installing CasConf and merging your first configuration files.

## Installation

### From PyPI (when published)

```bash
pip install casconf
```

### From Source

```bash
git clone https://github.com/ConsoleCatzirlI/casconf.git
cd casconf
pip install -e .
```

### Verify Installation

```bash
casconf --version
```

---

## Your First Merge

### Step 1: Create Sample Configuration Files

Create a directory structure with configuration files at different levels:

```bash
mkdir -p /etc/myapp ~/.config/myapp ./config
```

**System-level config** (`/etc/myapp/config.json`):

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "myapp"
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  },
  "features": {
    "cache": false,
    "analytics": false
  }
}
```

**User-level config** (`~/.config/myapp/config.json`):

```json
{
  "database": {
    "port": 5433
  },
  "logging": {
    "level": "DEBUG"
  },
  "features": {
    "cache": true
  }
}
```

**Project-level config** (`./config/config.json`):

```json
{
  "database": {
    "name": "myapp_dev"
  },
  "features": {
    "analytics": true
  }
}
```

### Step 2: Create a Discovery Configuration

Create `casconf.yaml` in your project directory:

```yaml
directories:
  - /etc/myapp
  - ~/.config/myapp
  - ./config

patterns:
  - "config.json"

merge_strategy: deep
```

### Step 3: Run CasConf

```bash
# Output merged config to stdout
casconf --discovery-config ./casconf.yaml
```

**Expected output:**

```json
{
  "database": {
    "host": "localhost",
    "port": 5433,
    "name": "myapp_dev"
  },
  "logging": {
    "level": "DEBUG",
    "format": "json"
  },
  "features": {
    "cache": true,
    "analytics": true
  }
}
```

Each directory's configuration cascades over the previous one, with later entries taking precedence for scalar values while nested objects are deep-merged.

### Step 4: Write Output to a File

```bash
casconf --discovery-config ./casconf.yaml --output ./merged.json
```

---

## Common Usage Patterns

### Environment-Based Configuration

Manage configuration for different deployment environments:

```yaml
# casconf.yaml
directories:
  - /etc/myapp
  - ~/.config/myapp
  - ./config/base
  - ./config/production  # or development, staging
```

```bash
# Switch environments by adjusting the discovery config
casconf --discovery-config ./casconf.production.yaml --output ./config.json
```

### User Overrides

Allow users to customize application behavior without modifying system files:

```yaml
# casconf.yaml
directories:
  - /etc/myapp          # system defaults (lowest priority)
  - /usr/local/etc/myapp
  - ~/.config/myapp     # user overrides (highest priority)

patterns:
  - "config.json"
  - "config.yaml"
```

### Plugin Configuration Aggregation

Merge configuration from multiple plugin directories:

```yaml
# casconf.yaml
directories:
  - ./config/base
  - ./plugins/auth/config
  - ./plugins/cache/config
  - ./plugins/metrics/config

patterns:
  - "*.config.json"
  - "defaults.json"
```

### Unix Pipeline Integration

CasConf outputs to stdout by default, making it a natural fit for Unix pipelines:

```bash
# Extract a specific key with jq
casconf | jq '.database.host'

# Filter YAML output with grep
casconf --format yaml | grep "host:"

# Pass config to another tool
casconf | my-app --config-stdin

# Transform and save
casconf | python -c "import sys,json; c=json.load(sys.stdin); c['extra']='value'; print(json.dumps(c))" > final.json

# Use in shell scripts
DB_HOST=$(casconf | jq -r '.database.host')
echo "Connecting to $DB_HOST"
```

---

## Library Usage Examples

### Basic Merge

```python
from casconf import merge_configs

# Returns merged configuration as a Python dict
config = merge_configs(discovery_config='./casconf.yaml')

print(config['database']['host'])  # localhost
print(config['logging']['level'])  # DEBUG
```

### Merge and Write to File

```python
from casconf import merge_configs

# Merge and write to file in a single call
merge_configs(
    discovery_config='./casconf.yaml',
    output='./merged.json',
    output_format='json'
)
```

### Programmatic Configuration

```python
from casconf import merge_configs, DiscoveryConfig

# Configure discovery programmatically without a file
discovery = DiscoveryConfig(
    directories=[
        '/etc/myapp',
        '~/.config/myapp',
        './config',
    ],
    patterns=['config.json', 'config.yaml'],
    merge_strategy='deep',
)

config = merge_configs(discovery_config=discovery)
```

### Validation

```python
from casconf import merge_configs, validate_config
from casconf.exceptions import CasConfValidationError

try:
    config = merge_configs(discovery_config='./casconf.yaml')
    validate_config(config, schema='./schema.json')
    print("Configuration is valid")
except CasConfValidationError as e:
    print(f"Invalid configuration: {e}")
```

### Application Integration

```python
import logging
from casconf import merge_configs
from casconf.exceptions import CasConfError

logger = logging.getLogger(__name__)

def load_app_config():
    try:
        config = merge_configs(
            discovery_config='./casconf.yaml',
            log_level=logging.DEBUG,
        )
        logger.info("Configuration loaded successfully")
        return config
    except CasConfError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise SystemExit(1)
```

---

## Advanced Features

### Verbose Output

See which files are being discovered and merged:

```bash
casconf --verbose --discovery-config ./casconf.yaml
```

Output:

```
[INFO] Scanning /etc/myapp for config.json ... found
[INFO] Scanning ~/.config/myapp for config.json ... found
[INFO] Scanning ./config for config.json ... found
[INFO] Merging 3 configuration files
[INFO] Writing to stdout
{ ... merged config ... }
```

### Multiple File Patterns

Discover and merge files matching multiple patterns:

```yaml
# casconf.yaml
directories:
  - /etc/myapp
  - ~/.config/myapp

patterns:
  - "config.json"
  - "config.yaml"
  - "*.conf.json"
  - "overrides.toml"
```

Files are discovered in pattern order within each directory, then merged in directory order.

### Format Conversion

Convert configuration between formats using CasConf:

```bash
# Read JSON configs, output as YAML
casconf --format yaml --output merged.yaml

# Read YAML configs, output as TOML
casconf --format toml --output merged.toml

# Read mixed formats, output as JSON (default)
casconf --output merged.json
```

---

## Troubleshooting

### No Configuration Files Found

```
Error: No configuration files found matching the discovery configuration.
```

**Solutions:**

1. Check that the directories in `casconf.yaml` exist and are readable.
2. Verify the file patterns match your actual file names.
3. Run with `--verbose` to see what directories are being scanned.

```bash
casconf --verbose
```

### Permission Denied

```
Error: Permission denied reading /etc/myapp/config.json
```

**Solutions:**

1. Check file permissions: `ls -la /etc/myapp/config.json`
2. Run with appropriate permissions or skip system directories.
3. Adjust your `casconf.yaml` to exclude inaccessible directories.

### Parse Error

```
Error: Failed to parse /path/to/config.json: Expecting value: line 5 column 3
```

**Solutions:**

1. Validate the file with a JSON/YAML linter.
2. Check for syntax errors (trailing commas, missing quotes).
3. Ensure the file encoding is UTF-8.

### Unexpected Merge Result

If the merged output doesn't look right:

1. Run with `--verbose` to see the merge order.
2. Check that your `casconf.yaml` directories are in the intended priority order (last directory wins for scalar values).
3. Review [DESIGN.md](DESIGN.md) for merge strategy details.

---

## Tips for Effective Usage

1. **Order directories by priority** - List directories from lowest to highest priority. Later entries override earlier ones.

2. **Use specific patterns** - Narrow patterns reduce the chance of accidentally merging unintended files.

3. **Keep the discovery config in version control** - Check in `casconf.yaml` alongside your project to ensure reproducible builds.

4. **Pipe to jq for inspection** - `casconf | jq '.'` gives you a formatted, colorized view of the merged configuration.

5. **Use YAML for human-edited configs** - YAML is more readable than JSON for hand-edited configuration files.

6. **Use JSON for machine-generated configs** - JSON is stricter and less error-prone for programmatically generated files.

7. **Separate concerns** - Keep infrastructure config (ports, hosts) separate from application config (feature flags, timeouts) using different pattern names.

---

See [API.md](API.md) for the complete library API reference.
