from enum import Enum

from .AppBaseModelDataDict import AppBaseModelDataDict
from .AppBaseModelNamesUUIDTagsDataDict import AppBaseModelNamesUUIDTagsDataDict
from .AppBaseModelUUIDTagsDataDict import AppBaseModelUUIDTagsDataDict
from .KnowledgebaseBaseModelDataDict import KnowledgebaseBaseModelDataDict
from .LedgerBaseModelDataDict import LedgerBaseModelDataDict
from .PersonDataDict import PersonDataDict

AppBaseModelDDictEnum = Enum(
    "AppBaseModelDDictEnum",
    {
        "AppBaseModelDataDict": AppBaseModelDataDict,
        "AppBaseModelNamesUUIDTagsDataDict": AppBaseModelNamesUUIDTagsDataDict,
        "AppBaseModelUUIDTagsDataDict": AppBaseModelUUIDTagsDataDict,
        "KnowledgebaseBaseModelDataDict": KnowledgebaseBaseModelDataDict,
        "LedgerBaseModelDataDict": LedgerBaseModelDataDict,
        "PersonDataDict": PersonDataDict,
    },
)


__all__ = [
    "AppBaseModelDDictEnum",
    "AppBaseModelDataDict",
    "AppBaseModelNamesUUIDTagsDataDict",
    "AppBaseModelUUIDTagsDataDict",
    "KnowledgebaseBaseModelDataDict",
    "LedgerBaseModelDataDict",
    "PersonDataDict",
]
