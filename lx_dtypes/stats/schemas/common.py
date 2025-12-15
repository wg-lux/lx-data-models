from typing import Any, Callable, cast

import pandera.engines.pandas_engine as pandas_engine

PANDERA_PYDANTIC_MODEL = cast(
    Callable[[type[Any]], Any],
    getattr(pandas_engine, "PydanticModel"),
)

COERCE = True
