"""Shared language policy and message catalogue loading for reporting and validation."""

from functools import lru_cache
from importlib.resources import files
from typing import Final, Literal, get_args

import yaml
from pydantic import TypeAdapter

LanguageCode = Literal["de", "en"]
DEFAULT_LANGUAGE: Final[LanguageCode] = "de"
LANGUAGE_LABELS: Final[dict[LanguageCode, str]] = {"de": "Deutsch", "en": "English"}


def validate_language(language: LanguageCode) -> None:
    if language not in get_args(LanguageCode):
        raise ValueError(f"Unsupported language: {language!r}.")


@lru_cache(maxsize=2)
def load_message_catalogue(filename: str) -> dict[LanguageCode, dict[str, str]]:
    text = files("lx_dtypes").joinpath(filename).read_text("utf-8")
    catalogue = TypeAdapter(dict[LanguageCode, dict[str, str]]).validate_python(
        yaml.safe_load(text), strict=True
    )
    if set(catalogue) != set(get_args(LanguageCode)):
        raise ValueError(f"Incomplete language catalogue: {filename}")
    return catalogue
