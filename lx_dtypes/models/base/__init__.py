from .app_base_model import AppBaseModelsLookupType, app_base_models_lookup
from .file.ddict import FileModelsDDictsLookupType, file_models_ddicts_lookup


# Pylint reports both TypedDict parents as the same base; the merge is intentional.
class BaseModelsLookupType(  # pylint: disable=duplicate-bases
    AppBaseModelsLookupType, FileModelsDDictsLookupType
):
    pass


base_model_ddicts = BaseModelsLookupType(
    **app_base_models_lookup,
    **file_models_ddicts_lookup,
)
