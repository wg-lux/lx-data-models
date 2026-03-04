from typing import Any, List

from pydantic import Field, field_validator

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES,
    FINDINGS_VALIDATOR_OPERATORS,
    FindingsValidatorOperator,
    FindingsValidatorQuery,
    _normalize_value_with_alias,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict import (
    FindingsValidatorDataDict,
)


class FindingsValidator(KnowledgebaseBaseModel[FindingsValidatorDataDict]):
    query: FindingsValidatorQuery = Field(default_factory=FindingsValidatorQuery)
    finding: str = Field(default_factory=str_unknown_factory)
    operator: FindingsValidatorOperator = "exists"

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, value: Any) -> Any:
        return _normalize_value_with_alias(
            value,
            field_name="findings_validator.operator",
            valid_values=FINDINGS_VALIDATOR_OPERATORS,
            deprecated_aliases=DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES,
        )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @property
    def ddict_class(self) -> type[FindingsValidatorDataDict]:
        return FindingsValidatorDataDict
