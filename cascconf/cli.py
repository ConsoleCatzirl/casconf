"""CascConf CLI — argument parsing and orchestration.

The :func:`main` function is the entry point registered in
``pyproject.toml``::

    [project.scripts]
    cascconf = "cascconf.cli:main"

It is also invoked when running ``python -m cascconf``.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from cascconf.discovery import DiscoveryConfig, discover
from cascconf.exceptions import CascConfError
from cascconf.merger import merge
from cascconf.parser import parse
from cascconf.writer import write

_ENV_DISCOVERY = "CASCCONF_DISCOVERY"
_ENV_LOG_LEVEL = "CASCCONF_LOG_LEVEL"
_DEFAULT_DISCOVERY = "cascconf.yaml"
_DEFAULT_FORMAT = "json"

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="cascconf",
        description=(
            "Deep-merge configuration files across multiple "
            "directories following a cascading pattern."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Output goes to stdout by default; pipe to other tools "
            "or use --output to write to a file.\n\n"
            "Examples:\n"
            "  cascconf\n"
            "  cascconf --output ./merged.json\n"
            "  cascconf --format yaml | grep host\n"
            "  cascconf | jq '.database'\n"
        ),
    )
    parser.add_argument(
        "--discovery-config",
        metavar="FILE",
        default=os.environ.get(_ENV_DISCOVERY, _DEFAULT_DISCOVERY),
        help=(
            "Path to the discovery configuration file "
            f"(default: {_DEFAULT_DISCOVERY!r}, or "
            f"${_ENV_DISCOVERY})"
        ),
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help=(
            "Write merged configuration to FILE instead of stdout."
        ),
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        metavar="FORMAT",
        default=_DEFAULT_FORMAT,
        choices=["json", "yaml", "toml"],
        help=(
            "Output format: json (default), yaml, or toml."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG) logging.",
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

        return f"cascconf {version('cascconf')}"
    except PackageNotFoundError:
        return "cascconf (version unknown)"


def _configure_logging(verbose: bool) -> None:
    """Configure root logging for the CLI.

    Args:
        verbose: If ``True``, set log level to DEBUG; otherwise use
            the value of ``$CASCCONF_LOG_LEVEL`` (default WARNING).
    """
    if verbose:
        level = logging.DEBUG
    else:
        env_level = os.environ.get(_ENV_LOG_LEVEL, "WARNING").upper()
        level = _LOG_LEVELS.get(env_level, logging.WARNING)

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
    )


def run(
    discovery_config: str | Path | DiscoveryConfig = _DEFAULT_DISCOVERY,
    output: str | Path | None = None,
    output_format: str = _DEFAULT_FORMAT,
    log_level: int = logging.WARNING,
) -> dict:
    """Discover, parse, merge, and optionally write configuration.

    This is the shared orchestration used by both the CLI entry point
    and the public library API.

    Args:
        discovery_config: Path to a discovery configuration file,
            or a :class:`~cascconf.discovery.DiscoveryConfig` object.
        output: Destination file path, or ``None`` to return the
            merged dict (and let the caller handle output).
        output_format: Serialisation format for file output.
        log_level: Python logging level for this run.

    Returns:
        The merged configuration as a ``dict``.

    Raises:
        CascConfError: On any configuration, parse, merge, or write
            error.
    """
    logging.getLogger("cascconf").setLevel(log_level)

    if not isinstance(discovery_config, DiscoveryConfig):
        discovery_config = DiscoveryConfig.from_file(
            Path(discovery_config)
        )

    paths = discover(discovery_config)
    configs = [parse(p) for p in paths]
    merged = merge(configs, strategy=discovery_config.merge_strategy)

    if output is not None:
        write(merged, output=output, fmt=output_format)

    return merged


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
        merged = run(
            discovery_config=args.discovery_config,
            output=args.output,
            output_format=args.output_format,
            log_level=(
                logging.DEBUG if args.verbose else logging.WARNING
            ),
        )
        if args.output is None:
            # Write to stdout
            write(merged, output=None, fmt=args.output_format)
    except CascConfError as exc:
        logging.getLogger("cascconf").error("%s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            f"Unexpected error: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0
