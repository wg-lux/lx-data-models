from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.names import UNIT_TYPE_MODEL_LIST_TYPE_FIELDS


class UnitType(KnowledgebaseBaseModel[UnitTypeDataDict]):
    @property
    def ddict_class(self) -> type[UnitTypeDataDict]:
        return UnitTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return UNIT_TYPE_MODEL_LIST_TYPE_FIELDS
