from .app_base_model import AppBaseModelsLookupType, app_base_models_lookup
from .file.ddict import FileModelsDDictsLookupType, file_models_ddicts_lookup


class BaseModelsLookupType(AppBaseModelsLookupType, FileModelsDDictsLookupType):
    pass


base_model_ddicts = BaseModelsLookupType(
    **app_base_models_lookup,
    **file_models_ddicts_lookup,
)
