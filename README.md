# CascConf

**Cascading Configuration Manager**

CascConf is a flexible configuration management tool that deep-merges configuration files across multiple directories following a cascading pattern. It embodies the Unix Philosophy: do one thing well.

## Overview

CascConf scans a configurable list of directories for matching configuration files and intelligently deep-merges them based on discovery order. The result is a single, unified configuration that respects the cascade hierarchy you define.

### Key Features

- **Deep Merging**: Recursively merges nested configuration structures
- **Format Agnostic**: Supports JSON, YAML, TOML, and INI formats
- **Dual Interface**: Use as a CLI tool or Python library
- **Configurable Discovery**: Define your own directory scan order
- **PEP 8 Compliant**: Clean, maintainable Python code
- **Unix Philosophy**: Does one thing well - merges configurations

## Use Cases

- Application configuration across development, staging, and production environments
- User-specific configuration overrides (system → user → project)
- Plugin or module configuration aggregation
- Multi-tenant configuration management
- Dotfile management and system configuration

## Quick Start

```bash
# Install
pip install cascconf

# Basic usage - merge configs and output to stdout
cascconf

# Output to a file
cascconf --output /path/to/output/config.json

# Specify custom discovery configuration
cascconf --discovery-config ./cascconf.yaml --output ./merged.json

# Use as a library
from cascconf import merge_configs

config = merge_configs(discovery_config='./cascconf.yaml')

# Or write directly to file
merge_configs(discovery_config='./cascconf.yaml', output='./merged.json')
```

See [USAGE.md](USAGE.md) for detailed examples.

## Project Status

🚧 **In Development** - This project is currently in the specification phase.

## Documentation

- [USAGE.md](USAGE.md) - Getting started guide with examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component overview
- [DESIGN.md](DESIGN.md) - Design decisions and rationale
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [API.md](API.md) - Library API reference

## Installation

```bash
# From PyPI (when published)
pip install cascconf

# From source
git clone https://github.com/ConsoleCatzirlI/cascconf.git
cd cascconf
pip install -e .
```

## Basic Usage

### Command-Line Interface

```bash
# Merge configs and output to stdout (default)
cascconf

# Output to a file
cascconf --output ./config.json

# Specify configuration file format for stdout
cascconf --format yaml

# Use custom discovery configuration
cascconf --discovery-config ./custom-discovery.yaml --output ./merged.json

# Pipe to other tools (Unix Philosophy)
cascconf | jq '.database'
cascconf --format yaml | grep "host:"
```

### Library Usage

```python
from cascconf import merge_configs

# Merge and return configuration data
config_data = merge_configs(discovery_config='./cascconf.yaml')

# Merge and write to file in one call
merge_configs(
    discovery_config='./cascconf.yaml',
    output='./output/config.json',
    output_format='json'
)
```

## Discovery Configuration

CascConf uses a discovery configuration file to determine where to search for configuration files:

```yaml
# cascconf.yaml
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
