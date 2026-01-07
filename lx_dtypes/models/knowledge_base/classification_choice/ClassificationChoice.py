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
        return CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationChoiceDataDict]:
        return ClassificationChoiceDataDict
