from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from lx_dtypes.models.contracts.json_types import JsonObject

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


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
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...

    def evaluate_findings_validator(
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...

    def evaluate_classification_validator(
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...

    def evaluate_intervention_validator(
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...

    def evaluate_unit_validator(
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...

    def evaluate_examination_validator(
        self, name: str, p_examination: "PExamination"
    ) -> JsonObject: ...


__all__ = ["KnowledgeBaseContract"]
