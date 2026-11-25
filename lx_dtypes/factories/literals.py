from typing import Literal


def str_unknown_factory() -> Literal["unknown"]:
    """
    Produce the literal string "unknown".

    Returns:
        Literal["unknown"]: The string "unknown".
    """
    return "unknown"


def normalize_missing_text(value: str | None) -> str:
    """Canonical absence for free text only; never apply to codes or relations.

    Preserve substantive text verbatim. The literal used by concept defaults is
    absent display text, as are NULL and the empty string.
    """
    return "" if value is None or value in ("", str_unknown_factory()) else value
