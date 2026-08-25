from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.finding.FindingDataDict import FindingDataDict
from lx_dtypes.names import FINDING_MODEL_LIST_TYPE_FIELDS


class Finding(KnowledgebaseBaseModel[FindingDataDict]):
    finding_types: str | list[str] = Field(default_factory=list_of_str_factory)
    classifications: str | list[str] = Field(default_factory=list_of_str_factory)
    interventions: str | list[str] = Field(default_factory=list_of_str_factory)
    caused_by_interventions: str | list[str] = Field(
        default_factory=list_of_str_factory
    )

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the field names that should be treated as list-typed for the Finding model.

        Returns:
            list_type_fields (List[str]): Names of fields in the model that are list-typed (e.g., 'finding_types', 'classifications', 'interventions').
        """
        return FINDING_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[FindingDataDict]:
        """
        Return the FindingDataDict type associated with this model.

        Returns:
            type[FindingDataDict]: The data-dictionary class used for Finding model instances.
        """
        return FindingDataDict
