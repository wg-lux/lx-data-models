from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.names import UNIT_TYPE_MODEL_LIST_TYPE_FIELDS


class UnitType(KnowledgebaseBaseModel[UnitTypeDataDict]):
    @property
    def ddict_class(self) -> type[UnitTypeDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            type[UnitTypeDataDict]: The UnitTypeDataDict class used as the model's underlying data dictionary type.
        """
        return UnitTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Get the field names used when producing lists of UnitType models.

        Returns:
            list[str]: Field names included when listing UnitType models.
        """
        return UNIT_TYPE_MODEL_LIST_TYPE_FIELDS
