from typing import TypedDict

from .AppBaseModel import AppBaseModel
from .AppBaseModelNamesUUIDTags import AppBaseModelNamesUUIDTags
from .AppBaseModelUUIDTags import AppBaseModelUUIDTags
from .KnowledgebaseBaseModel import KnowledgebaseBaseModel

# from .LedgerBaseModel import LedgerBaseModel
# from .PersonModel import PersonModel


class AppBaseModelsPydanticLookup(TypedDict):
    AppBaseModel: type[AppBaseModel]
    AppBaseModelNamesUUIDTags: type[AppBaseModelNamesUUIDTags]
    AppBaseModelUUIDTags: type[AppBaseModelUUIDTags]
    # KnowledgebaseBaseModel: type[KnowledgebaseBaseModel] # remove as this is an abstract class
    # LedgerBaseModel: type[LedgerBaseModel]
    # PersonModel: type[PersonModel]


app_base_models_pydantic_lookup = AppBaseModelsPydanticLookup(
    AppBaseModel=AppBaseModel,
    AppBaseModelNamesUUIDTags=AppBaseModelNamesUUIDTags,
    AppBaseModelUUIDTags=AppBaseModelUUIDTags,
    # KnowledgebaseBaseModel=KnowledgebaseBaseModel,
    # LedgerBaseModel=LedgerBaseModel,
    # PersonModel=PersonModel,
)

__all__ = [
    "app_base_models_pydantic_lookup",
    "AppBaseModelsPydanticLookup",
    "AppBaseModel",
    "AppBaseModelNamesUUIDTags",
    "AppBaseModelUUIDTags",
    "KnowledgebaseBaseModel",
    # "LedgerBaseModel",
    # "PersonModel",
]
