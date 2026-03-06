# CascConf

**CascConf** (Cascading Configuration) is a command-line tool and Python library for deep-merging configuration settings discovered across multiple directories and files.

## Overview

CascConf follows the [Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy): do one thing well, work with text streams, and compose easily with other tools. It scans a configurable list of directories for matching configuration files, deep-merges those files in discovery order, and emits the result to stdout or a file.

## Features

- **Deep merge** — nested keys from later sources override or extend earlier sources rather than replacing entire objects.
- **Ordered discovery** — directories are scanned in a user-defined order; files discovered later take precedence.
- **Pluggable formats** — supports YAML, JSON, and TOML configuration files out of the box.
- **Dual-mode usage** — run as a CLI tool *or* import as a Python library.
- **Unix-friendly** — reads from stdin, writes to stdout, integrates seamlessly with pipes and shell scripts.

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for installation instructions and usage examples.

## Documentation

| Document | Description |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Installation, basic usage, and common recipes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow, and component overview |
| [API.md](API.md) | Python library API reference |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute to CascConf |

## License

CascConf is released under the [GNU Affero General Public License v3.0](LICENSE).
