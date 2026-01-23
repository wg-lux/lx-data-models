from typing import TypedDict

from .AppBaseModelDataDict import AppBaseModelDataDict
from .AppBaseModelNamesUUIDTagsDataDict import AppBaseModelNamesUUIDTagsDataDict
from .AppBaseModelUUIDTagsDataDict import AppBaseModelUUIDTagsDataDict
from .KnowledgebaseBaseModelDataDict import KnowledgebaseBaseModelDataDict
from .LedgerBaseModelDataDict import LedgerBaseModelDataDict
from .PersonDataDict import PersonDataDict


class AppBaseModelsDDictsLookupType(TypedDict):
    AppBaseModelDataDict: type[AppBaseModelDataDict]
    AppBaseModelNamesUUIDTagsDataDict: type[AppBaseModelNamesUUIDTagsDataDict]
    AppBaseModelUUIDTagsDataDict: type[AppBaseModelUUIDTagsDataDict]
    KnowledgebaseBaseModelDataDict: type[KnowledgebaseBaseModelDataDict]
    LedgerBaseModelDataDict: type[LedgerBaseModelDataDict]
    PersonDataDict: type[PersonDataDict]


app_base_models_ddicts_lookup = AppBaseModelsDDictsLookupType(
    AppBaseModelDataDict=AppBaseModelDataDict,
    AppBaseModelNamesUUIDTagsDataDict=AppBaseModelNamesUUIDTagsDataDict,
    AppBaseModelUUIDTagsDataDict=AppBaseModelUUIDTagsDataDict,
    KnowledgebaseBaseModelDataDict=KnowledgebaseBaseModelDataDict,
    LedgerBaseModelDataDict=LedgerBaseModelDataDict,
    PersonDataDict=PersonDataDict,
)

__all__ = [
    "AppBaseModelDataDict",
    "app_base_models_ddicts_lookup",
    "AppBaseModelsDDictsLookupType",
    "AppBaseModelNamesUUIDTagsDataDict",
    "AppBaseModelUUIDTagsDataDict",
    "KnowledgebaseBaseModelDataDict",
    "LedgerBaseModelDataDict",
    "PersonDataDict",
]
