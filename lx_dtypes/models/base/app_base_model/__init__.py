from .ddict import (
    AppBaseModelsDDictsLookupType,
    app_base_models_ddicts_lookup,
)
from .pydantic import (
    AppBaseModelsPydanticLookup,
    app_base_models_pydantic_lookup,
)


class AppBaseModelsLookupType(
    AppBaseModelsPydanticLookup, AppBaseModelsDDictsLookupType
):
    pass


app_base_models_lookup = AppBaseModelsLookupType(
    **app_base_models_pydantic_lookup,
    **app_base_models_ddicts_lookup,
)
