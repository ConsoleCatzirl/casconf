"""CasConf merger engine.

Implements deep and shallow merge strategies for combining
multiple configuration dictionaries into one.

The primary public symbol is :func:`merge` which dispatches to the
appropriate strategy based on the ``strategy`` parameter.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_VALID_STRATEGIES = frozenset({"deep", "shallow"})
_VALID_LIST_STRATEGIES = frozenset({"append", "replace"})


def merge(
    configs: list[dict[str, Any]],
    strategy: str = "deep",
    list_strategy: str = "append",
) -> dict[str, Any]:
    """Merge an ordered list of configuration dicts.

    Configs are applied left-to-right; later entries take
    precedence over earlier ones.

    Args:
        configs: Ordered list of configuration dicts to merge.
            The first element has the lowest priority.
        strategy: Merge strategy.  One of ``'deep'`` (default)
            or ``'shallow'``.
        list_strategy: How lists are merged during deep merge.
            One of ``'append'`` (default, concatenates lists) or
            ``'replace'`` (override list replaces base list).
            Only applies when *strategy* is ``'deep'``.

    Returns:
        A new dict representing the merged configuration.

    Raises:
        ValueError: If *strategy* or *list_strategy* is not a recognised value.
    """
    if strategy not in _VALID_STRATEGIES:
        raise ValueError(f"Unknown merge strategy {strategy!r}. Must be one of: {sorted(_VALID_STRATEGIES)}")
    if list_strategy not in _VALID_LIST_STRATEGIES:
        raise ValueError(f"Unknown list merge strategy {list_strategy!r}. Must be one of: {sorted(_VALID_LIST_STRATEGIES)}")

    if not configs:
        return {}

    result: dict[str, Any] = {}
    if strategy == "deep":

        def merge_fn(b: dict[str, Any], o: dict[str, Any]) -> dict[str, Any]:
            return deep_merge(b, o, list_strategy=list_strategy)

    else:
        merge_fn = shallow_merge  # type: ignore[assignment]
    for config in configs:
        result = merge_fn(result, config)
    return result


def deep_merge(
    base: dict[str, Any],
    override: dict[str, Any],
    list_strategy: str = "append",
) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict.

    - Scalar values in *override* replace those in *base*.
    - Dict values are merged recursively.
    - List values are concatenated when *list_strategy* is ``'append'``
      (*override* appended to *base*), or replaced entirely when
      *list_strategy* is ``'replace'``.
    - Type conflicts (e.g. scalar vs dict) log a warning; the
      *override* value wins.

    Args:
        base: The base configuration dictionary.
        override: The overriding configuration dictionary.
        list_strategy: How lists are merged.  One of ``'append'``
            (default) or ``'replace'``.

    Returns:
        A new dict representing the deep-merged result.
    """
    result = base.copy()
    for key, value in override.items():
        base_value = result.get(key)
        if isinstance(base_value, dict) and isinstance(value, dict):
            result[key] = deep_merge(base_value, value, list_strategy=list_strategy)
        elif isinstance(base_value, list) and isinstance(value, list):
            result[key] = base_value + value if list_strategy == "append" else value
        else:
            if key in result and type(base_value) is not type(value):
                logger.warning(
                    "Type conflict at key %r: %s overrides %s",
                    key,
                    type(value).__name__,
                    type(base_value).__name__,
                )
            result[key] = value
    return result


def shallow_merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """Merge *override* into *base* at the top level only.

    Top-level keys from *override* replace those in *base*
    entirely, without recursing into nested dicts or lists.

    Args:
        base: The base configuration dictionary.
        override: The overriding configuration dictionary.

    Returns:
        A new dict representing the shallow-merged result.
    """
    result = base.copy()
    result.update(override)
    return result
