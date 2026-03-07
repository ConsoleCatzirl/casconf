# CasConf

**Cascading Configuration Manager**

CasConf is a flexible configuration management tool that deep-merges configuration files across multiple directories following a cascading pattern.

## Overview

CasConf scans a configurable list of directories for matching configuration files and intelligently deep-merges them based on discovery order. The result is a single, unified configuration that respects the cascade hierarchy you define.

### Key Features

- **Deep Merging**: Recursively merges nested configuration structures
- **Format Agnostic**: Supports JSON, YAML, TOML, and INI formats
- **Configurable Discovery**: Define your own directory scan order

## Use Cases

- Application configuration across development, staging, and production environments
- User-specific configuration overrides (system → user → project)
- Plugin or module configuration aggregation
- Multi-tenant configuration management
- Dotfile management and system configuration

## Quick Start

```bash
# Install
pip install casconf

# Basic usage - merge configs and output to stdout
casconf --discovery-config ./casconf.yaml

# Output to a file
casconf --discovery-config ./casconf.yaml --output config.json

# Specify discovery configuration via environment variable
CASCONF_DISCOVERY=./casconf.yaml casconf
```

```python
# Use as a library
from casconf import merge_configs

config = merge_configs(discovery_config='./casconf.yaml')

# Or write directly to file
merge_configs(discovery_config='./casconf.yaml', output='./merged.json')
```

See [USAGE.md](USAGE.md) for detailed examples.

## Documentation

- [USAGE.md](USAGE.md) - Getting started guide with examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component overview
- [DESIGN.md](DESIGN.md) - Design decisions and rationale
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [API.md](API.md) - Library API reference

## Installation

```bash
# From PyPI (when published)
pip install casconf

# From source
pip install git+https://github.com/ConsoleCatzirl/casconf.git@main
```

## Basic Usage

### Command-Line Interface

```bash
# Merge configs and output to stdout (default)
casconf

# Output to a file
casconf --output ./config.json

# Specify configuration file format for stdout
casconf --format yaml

# Use custom discovery configuration
casconf --discovery-config ./custom-discovery.yaml --output ./merged.json

# Pipe to other tools
casconf | jq '.database'
casconf --format yaml | grep "host:"
```

### Library Usage

```python
from casconf import merge_configs

# Merge and return configuration data
config_data = merge_configs(discovery_config='./casconf.yaml')

# Merge and write to file in one call
merge_configs(
    discovery_config='./casconf.yaml',
    output='./output/config.json',
    output_format='json'
)
```

## Discovery Configuration

CasConf uses a discovery configuration file to determine where to search for configuration files:

```yaml
# casconf.yaml
directories:
  - /etc/myapp
  - ~/.config/myapp
  - ./config

patterns:
  - "config.json"
  - "config.yaml"
  - "*.conf.json"

merge_strategy: deep  # or 'shallow'
```

## License

This project is dual-licensed:

- **MIT License**: When used as a standalone executable (CLI tool)
- **GNU General Public License v3.0 (GPL-3.0)**: When imported or linked as a library

See [LICENSE](LICENSE) for full details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

This project follows PEP 8 style guidelines and emphasizes simplicity and maintainability.
