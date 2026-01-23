from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.names import CLASSIFICATION_MODEL_LIST_TYPE_FIELDS

from .ClassificationDataDict import ClassificationDataDict


class Classification(
    KnowledgebaseBaseModel[ClassificationDataDict],
):
    classification_choices: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )
    classification_types: Union[str, List[str]] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the names of model fields that should be treated as list types.

        Returns:
            A list of field names that are considered list-typed for this model.
        """
        return CLASSIFICATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationDataDict]:
        """
        The data-dictionary class associated with this model.

        Returns:
            ddict_class_type (type[ClassificationDataDict]): The ClassificationDataDict type used by this model.
        """
        return ClassificationDataDict
