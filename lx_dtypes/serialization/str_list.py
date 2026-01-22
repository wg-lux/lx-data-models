from __future__ import annotations

from collections.abc import Sequence
from typing import Final

_WHITESPACE_ONLY: Final = ""


def parse_str_list(value: Sequence[str] | str | None) -> list[str]:
    """Normalize comma-separated strings or sequences into a list of strings.

    Args:
        value: Input that can already be a sequence of strings, a comma-separated
            string, or ``None``.

    Returns:
        list[str]: Cleaned list of non-empty strings stripped of whitespace.

    Raises:
        TypeError: If the input is neither a string, ``None``, nor a sequence of
            strings.
    """

    if value is None:
        return []

    if isinstance(value, str):
        raw_items: Sequence[str] = value.split(",")
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        raw_items = value
    else:
        raise TypeError(
            "Expected comma-separated string or sequence of strings for list field."
        )

    items: list[str] = []
    for item in raw_items:
        if not isinstance(item, str):
            raise TypeError("All elements inside the list field must be strings.")
        stripped = item.strip()
        if stripped != _WHITESPACE_ONLY:
            items.append(stripped)

    return items


def serialize_str_list(values: Sequence[str] | None, sep: str = ",") -> str:
    """Serialize a list of strings into a comma-separated string.

    Args:
        values: Sequence of string values to serialize. ``None`` is treated as an
            empty sequence.

    Returns:
        str: Comma-separated string with whitespace-trimmed, non-empty items.
    """

    if not values:
        return _WHITESPACE_ONLY

    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise TypeError("All elements inside the list field must be strings.")
        stripped = value.strip()
        if stripped != _WHITESPACE_ONLY:
            normalized.append(stripped)

    return sep.join(normalized)
