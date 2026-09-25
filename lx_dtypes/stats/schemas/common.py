from collections.abc import Callable
from typing import Any, cast

from pandera.engines import pandas_engine

PANDERA_PYDANTIC_MODEL = cast(
    Callable[[type[Any]], Any],
    pandas_engine.PydanticModel,
)

COERCE = True
