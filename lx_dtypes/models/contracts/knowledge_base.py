from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.contracts.json_types import JsonObject

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class KnowledgeBaseIdentity(BaseModel):
    """Canonical, complete identity of one knowledge-base artifact."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
    )

    knowledge_base_module: str = Field(min_length=1)
    knowledge_base_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def reject_ambiguous_segments(self) -> Self:
        for field_name, value in (
            ("knowledge_base_module", self.knowledge_base_module),
            ("knowledge_base_version", self.knowledge_base_version),
        ):
            if "@" in value:
                raise ValueError(f"{field_name} must not contain '@'")
        return self

    @property
    def canonical_name(self) -> str:
        """Return the stable ``module@version`` representation."""

        return f"{self.knowledge_base_module}@{self.knowledge_base_version}"


def validate_optional_knowledge_base_identity(
    module_name: str | None,
    version: str | None,
) -> KnowledgeBaseIdentity | None:
    """Validate an optional identity while rejecting half-specified pairs."""

    if module_name is None and version is None:
        return None
    if module_name is None or version is None:
        raise ValueError(
            "knowledge_base_module and knowledge_base_version must be provided together"
        )
    return KnowledgeBaseIdentity(
        knowledge_base_module=module_name,
        knowledge_base_version=version,
    )


class KnowledgeBaseContract(Protocol):
    """Typed API surface used by patient and reporting endpoints."""

    report_template: JsonObject
    findings_validator: JsonObject
    classification_validator: JsonObject
    intervention_validator: JsonObject
    unit_validator: JsonObject
    examination_validator: JsonObject

    def export_core_concepts(self) -> JsonObject: ...

    def export_report_template(self, name: str) -> JsonObject: ...

    def export_report_template_preview(self, name: str) -> JsonObject: ...

    def get_report_template_lifecycle_status(self, name: str) -> str: ...

    def evaluate_report_template_validators(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...

    def evaluate_findings_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...

    def evaluate_classification_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...

    def evaluate_intervention_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...

    def evaluate_unit_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...

    def evaluate_examination_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject: ...


__all__ = [
    "KnowledgeBaseContract",
    "KnowledgeBaseIdentity",
    "validate_optional_knowledge_base_identity",
]
