"""Reference catalogues participate in standard package resolution and export."""

from typing import TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.reference_catalog import ReferenceCatalogPayload


class ReferenceCatalogDataDict(KnowledgebaseBaseModelDataDict):
    payload: JsonObject


class ReferenceCatalog(KnowledgebaseBaseModel[ReferenceCatalogDataDict]):
    payload: ReferenceCatalogPayload

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[ReferenceCatalogDataDict]:
        return ReferenceCatalogDataDict


class KbReferenceCatalogLookupType(TypedDict):
    ReferenceCatalog: type[ReferenceCatalog]
