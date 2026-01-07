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
        return UnitDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return UNIT_MODEL_LIST_TYPE_FIELDS

    @model_validator(mode="after")
    def fallback_abbreviation(self) -> Self:
        """Autofill missing abbreviation with the primary name. Truncate to 10 characters."""
        if not self.abbreviation:
            abbr = self.name
            if len(abbr) > 10:
                abbr = abbr[:10]
            self.abbreviation = abbr

        return self
