"""CasConf CLI — argument parsing and orchestration.

The :func:`main` function is the entry point registered in
``pyproject.toml``::

    [project.scripts]
    casconf = casconf.cli:main"

It is also invoked when running ``python -m casconf``.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from casconf.api import (
    _DEFAULT_DISCOVERY,
    _ENV_DISCOVERY,
    merge_configs,
)
from casconf.exceptions import CasConfError
from casconf.writer import write

_ENV_LOG_LEVEL = "CASCONF_LOG_LEVEL"
_ENV_OUTPUT = "CASCONF_OUTPUT"
_ENV_FORMAT = "CASCONF_FORMAT"
_ENV_VERBOSE = "CASCONF_VERBOSE"
_DEFAULT_FORMAT = "json"


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    _default_verbose = os.environ.get(_ENV_VERBOSE, "").lower() in ("1", "true", "yes")
    parser = argparse.ArgumentParser(
        prog="casconf",
        description="Deep-merge configuration files across multiple directories following a cascading pattern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Output goes to stdout by default; pipe to other tools "
            "or use --output to write to a file.\n\n"
            "All options can also be set via environment variables:\n"
            f"  ${_ENV_DISCOVERY}  -- discovery config file path\n"
            f"  ${_ENV_OUTPUT}     -- output file path\n"
            f"  ${_ENV_FORMAT}     -- output format (json, yaml, toml)\n"
            f"  ${_ENV_VERBOSE}    -- enable verbose logging (1/true/yes)\n"
            f"  ${_ENV_LOG_LEVEL}  -- log level (DEBUG/INFO/WARNING/ERROR)\n\n"
            "Examples:\n"
            "  casconf\n"
            "  casconf --output ./merged.json\n"
            "  casconf --format yaml | grep host\n"
            "  casconf | jq '.database'\n"
        ),
    )
    parser.add_argument(
        "--discovery-config",
        metavar="FILE",
        default=os.environ.get(_ENV_DISCOVERY, _DEFAULT_DISCOVERY),
        help=(f"Path to the discovery configuration file (default: {_DEFAULT_DISCOVERY!r}, or ${_ENV_DISCOVERY})"),
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=os.environ.get(_ENV_OUTPUT),
        help=(f"Write merged configuration to FILE instead of stdout (or ${_ENV_OUTPUT})."),
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        metavar="FORMAT",
        default=os.environ.get(_ENV_FORMAT, _DEFAULT_FORMAT),
        choices=["json", "yaml", "toml"],
        help=(f"Output format: json (default), yaml, or toml (or ${_ENV_FORMAT})."),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=_default_verbose,
        help=f"Enable verbose (DEBUG) logging (or set ${_ENV_VERBOSE}=1).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_get_version(),
    )
    return parser


def _get_version() -> str:
    """Return the installed package version string.

    Uses :func:`importlib.metadata.version` to read the version that
    pbr wrote into the package metadata at install time.  Falls back
    to a placeholder string when the package is not installed (e.g.
    when running directly from a source checkout without ``pip install
    -e .``).
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        return f"casconf {version('casconf')}"
    except PackageNotFoundError:
        return "casconf (version unknown)"


def _configure_logging(verbose: bool) -> None:
    """Configure root logging for the CLI.

    Args:
        verbose: If ``True``, set log level to DEBUG; otherwise use
            the value of ``$CASCONF_LOG_LEVEL`` (default WARNING).
    """
    if verbose:
        level = logging.DEBUG
    else:
        env_level = os.environ.get(_ENV_LOG_LEVEL, "WARNING").upper()
        level = getattr(logging, env_level, logging.WARNING)

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]`` when
            ``None``).

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    arg_parser = _build_parser()
    args = arg_parser.parse_args(argv)
    _configure_logging(args.verbose)

    try:
        merged = merge_configs(
            discovery_config=args.discovery_config,
            output_format=args.output_format,
            log_level=(logging.DEBUG if args.verbose else logging.WARNING),
        )
        assert merged is not None
        write(merged, output=args.output, fmt=args.output_format)
    except CasConfError as exc:
        logging.getLogger("casconf").error("%s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            f"Unexpected error: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0
