from collections.abc import Callable
from typing import Any, cast

from pandera.engines import pandas_engine
from pandera.engines.type_aliases import PandasObject


# Pandera's immutable decorator obscures this runtime class from Pyright.
class _EmptyAwarePydanticModel(pandas_engine.PydanticModel):  # pyright: ignore[reportGeneralTypeIssues]
    """Validate empty export columns without attempting row coercion."""

    def coerce(self, data_container: PandasObject) -> PandasObject:
        if data_container.empty:
            # Pandera stores the Pydantic model class in `type`; pylint infers a Field.
            model_fields = self.type.model_fields  # pylint: disable=no-member
            self._check_column_names(data_container, list(model_fields))
            return data_container
        return super().coerce(data_container)


PANDERA_PYDANTIC_MODEL = cast(
    Callable[[type[Any]], Any],
    _EmptyAwarePydanticModel,
)

COERCE = True
