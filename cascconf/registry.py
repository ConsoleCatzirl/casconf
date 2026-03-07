"""CascConf configuration registry.

Maps file extensions and format names to parser and writer
callables.  New formats can be registered at runtime without
modifying core code (Registry pattern).

Usage::

    from cascconf.registry import registry

    # Look up a parser by extension
    parse_fn = registry.get_parser(".json")
    data = parse_fn(path)

    # Register a custom parser
    registry.register_parser(".custom", my_parse_fn)
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Callable, cast

# Type aliases
ParserFn = Callable[[Path], dict[str, Any]]
WriterFn = Callable[[dict[str, Any], io.TextIOBase], None]


class Registry:
    """Map format identifiers to parser and writer callables.

    Attributes:
        _parsers: Mapping of lowercase file extension (e.g. ``'.json'``)
            to a callable that reads the file and returns a dict.
        _writers: Mapping of lowercase format name (e.g. ``'json'``)
            to a callable that serialises a dict to a text stream.
    """

    def __init__(self) -> None:
        self._parsers: dict[str, ParserFn] = {}
        self._writers: dict[str, WriterFn] = {}

    # ------------------------------------------------------------------
    # Parser registration / lookup
    # ------------------------------------------------------------------

    def register_parser(self, extension: str, fn: ParserFn) -> None:
        """Register a parser callable for the given file extension.

        Args:
            extension: Lowercase file extension including the leading
                dot, e.g. ``'.json'`` or ``'.yaml'``.
            fn: Callable that accepts a :class:`~pathlib.Path` and
                returns a ``dict``.
        """
        self._parsers[extension.lower()] = fn

    def get_parser(self, extension: str) -> ParserFn | None:
        """Return the parser for *extension*, or ``None`` if unknown.

        Args:
            extension: Lowercase file extension, e.g. ``'.json'``.

        Returns:
            The registered parser callable, or ``None``.
        """
        return self._parsers.get(extension.lower())

    @property
    def supported_extensions(self) -> list[str]:
        """Sorted list of registered file extensions."""
        return sorted(self._parsers.keys())

    # ------------------------------------------------------------------
    # Writer registration / lookup
    # ------------------------------------------------------------------

    def register_writer(self, fmt: str, fn: WriterFn) -> None:
        """Register a writer callable for the given format name.

        Args:
            fmt: Lowercase format name, e.g. ``'json'`` or ``'yaml'``.
            fn: Callable that accepts a dict and a writable text
                stream and serialises the dict.
        """
        self._writers[fmt.lower()] = fn

    def get_writer(self, fmt: str) -> WriterFn | None:
        """Return the writer for *fmt*, or ``None`` if unknown.

        Args:
            fmt: Lowercase format name, e.g. ``'json'``.

        Returns:
            The registered writer callable, or ``None``.
        """
        return self._writers.get(fmt.lower())

    @property
    def supported_formats(self) -> list[str]:
        """Sorted list of registered output format names."""
        return sorted(self._writers.keys())


# ---------------------------------------------------------------------------
# Built-in parsers
# ---------------------------------------------------------------------------


def _parse_json(path: Path) -> dict[str, Any]:
    """Parse a JSON file and return a dict."""
    import json

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)  # type: ignore[no-any-return]


def _parse_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file and return a dict."""
    try:
        import yaml  # pyyaml
    except ImportError as exc:
        raise ImportError("YAML support requires the 'pyyaml' package. Install it with: pip install cascconf[yaml]") from exc

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    result = yaml.safe_load(text)
    return result if isinstance(result, dict) else {}


def _parse_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file and return a dict."""
    try:
        import tomllib  # type: ignore[import-not-found]  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError as exc:
            raise ImportError(
                "TOML support on Python <3.11 requires the 'tomli' package. Install it with: pip install cascconf[toml]"
            ) from exc

    return cast(dict[str, Any], tomllib.loads(path.read_text(encoding="utf-8")))


def _parse_ini(path: Path) -> dict[str, Any]:
    """Parse an INI/CFG file and return a dict."""
    import configparser

    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    result: dict[str, Any] = {}
    for section in parser.sections():
        result[section] = dict(parser[section])
    return result


# ---------------------------------------------------------------------------
# Built-in writers
# ---------------------------------------------------------------------------


def _write_json(data: dict[str, Any], stream: io.TextIOBase) -> None:
    """Serialise *data* to *stream* as JSON."""
    import json

    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")


def _write_yaml(data: dict[str, Any], stream: io.TextIOBase) -> None:
    """Serialise *data* to *stream* as YAML."""
    try:
        import yaml  # pyyaml
    except ImportError as exc:
        raise ImportError(
            "YAML support requires the 'pyyaml' package. " "Install it with: pip install cascconf[yaml]"
        ) from exc

    yaml.dump(
        data,
        stream,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    )


def _write_toml(data: dict[str, Any], stream: io.TextIOBase) -> None:
    """Serialise *data* to *stream* as TOML."""
    try:
        import tomli_w
    except ImportError as exc:
        raise ImportError(
            "TOML write support requires the 'tomli-w' package. Install it with: pip install cascconf[toml]"
        ) from exc

    stream.write(tomli_w.dumps(data))


# ---------------------------------------------------------------------------
# Singleton registry with built-in formats pre-registered
# ---------------------------------------------------------------------------

registry = Registry()

registry.register_parser(".json", _parse_json)
registry.register_parser(".yaml", _parse_yaml)
registry.register_parser(".yml", _parse_yaml)
registry.register_parser(".toml", _parse_toml)
registry.register_parser(".ini", _parse_ini)
registry.register_parser(".cfg", _parse_ini)

registry.register_writer("json", _write_json)
registry.register_writer("yaml", _write_yaml)
registry.register_writer("toml", _write_toml)
