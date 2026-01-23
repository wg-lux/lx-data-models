from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDataDict import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.names import (
    CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS,
)


class ClassificationChoice(KnowledgebaseBaseModel[ClassificationChoiceDataDict]):
    classification_choice_descriptors: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Return the list-type field names for the ClassificationChoice model.

        Returns:
            List[str]: Field names that must be treated as list types for this model.
        """
        return CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationChoiceDataDict]:
        """
        Return the associated data-dictionary class for this model.

        Returns:
            type[ClassificationChoiceDataDict]: The ClassificationChoiceDataDict class used as the model's data-dictionary type.
        """
        return ClassificationChoiceDataDict
