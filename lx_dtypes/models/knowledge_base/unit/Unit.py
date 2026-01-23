from typing import List, Optional, Self

from pydantic import model_validator

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import UnitDataDict
from lx_dtypes.names import UNIT_MODEL_LIST_TYPE_FIELDS


class Unit(KnowledgebaseBaseModel[UnitDataDict]):
    abbreviation: Optional[str] = None
    unit_types: List[str]

    @property
    def ddict_class(self) -> type[UnitDataDict]:
        """
        Return the UnitDataDict class associated with this model.

        Returns:
            type[UnitDataDict]: The UnitDataDict class used by this Unit model.
        """
        return UnitDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the model field names that should be treated as list-type fields.

        Returns:
            list[str]: Field name strings that the model treats as list-type fields.
        """
        return UNIT_MODEL_LIST_TYPE_FIELDS

    @model_validator(mode="after")
    def fallback_abbreviation(self) -> Self:
        """
        Fill the missing abbreviation from the model's name, truncating it to 10 characters if necessary.

        Returns:
            Self: the instance, with `abbreviation` set to the primary `name` (truncated to 10 characters) if it was previously missing.
        """
        if not self.abbreviation:
            abbr = self.name
            if len(abbr) > 10:
                abbr = abbr[:10]
            self.abbreviation = abbr

        return self
