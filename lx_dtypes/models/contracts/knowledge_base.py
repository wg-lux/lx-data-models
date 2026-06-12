from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class KnowledgeBaseContract(Protocol):
    """Typed API surface used by patient and reporting endpoints."""

    report_template: dict[str, Any]
    findings_validator: dict[str, Any]
    classification_validator: dict[str, Any]
    intervention_validator: dict[str, Any]
    unit_validator: dict[str, Any]
    examination_validator: dict[str, Any]

    def export_core_concepts(self) -> dict[str, Any]: ...

    def export_report_template(self, name: str) -> dict[str, Any]: ...

    def export_report_template_preview(self, name: str) -> dict[str, Any]: ...

    def get_report_template_lifecycle_status(self, name: str) -> str: ...

    def evaluate_report_template_validators(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...

    def evaluate_findings_validator(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...

    def evaluate_classification_validator(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...

    def evaluate_intervention_validator(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...

    def evaluate_unit_validator(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...

    def evaluate_examination_validator(
        self, name: str, p_examination: "PExamination"
    ) -> dict[str, Any]: ...


__all__ = ["KnowledgeBaseContract"]
