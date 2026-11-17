"""Core-concept and FHIR exchange adapters for a knowledge base."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.models.contracts import kb_to_core_concepts_payload
from lx_dtypes.models.contracts.finding_extraction import FindingTextExtractor
from lx_dtypes.models.knowledge_base.fhir.findings import (
    FhirTerminologyValidatedFindingResultDataDict,
    export_terminology_validated_fhir_observations,
    import_terminology_validated_fhir_observations,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


class KnowledgeBaseInterop:
    """Core-concept and FHIR exchange adapters for a knowledge base."""

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def export_core_concepts(self) -> dict[str, Any]:
        """
        Export canonical core concept payloads for frontend consumption.
        """
        payload = kb_to_core_concepts_payload(self.kb)
        return payload.model_dump(mode="json")

    def export_fhir_terminology(
        self,
        *,
        base_url: str = "https://wg-lux.de/fhir",
        publisher: str = "Working Group Lux",
        bundle: bool = False,
        medical_field: str | None = None,
    ) -> dict[str, Any]:
        """
        Export core KB terminology as FHIR CodeSystem and ValueSet resources.
        """
        from lx_dtypes.models.knowledge_base.fhir.terminology import (
            export_fhir_terminology,
            export_fhir_terminology_bundle,
        )

        if bundle:
            return export_fhir_terminology_bundle(
                self.kb,
                base_url=base_url,
                publisher=publisher,
                medical_field=medical_field,
            )
        return export_fhir_terminology(
            self.kb,
            base_url=base_url,
            publisher=publisher,
            medical_field=medical_field,
        )

    @staticmethod
    def import_fhir_terminology(
        payload: Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        module_name: str = "fhir_import",
        language: str | None = None,
    ) -> dict[str, Any]:
        """
        Import FHIR CodeSystem resources into KB storage-compatible concepts.
        """
        from lx_dtypes.models.knowledge_base.fhir.terminology import (
            import_fhir_terminology,
        )

        return import_fhir_terminology(
            payload,
            module_name=module_name,
            language=language,
        )

    @staticmethod
    def from_fhir(
        payload: Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        module_name: str = "fhir_import",
        version: str | None = None,
        medical_field: str | None = None,
        author: str | None = None,
        language: str | None = None,
        strict: bool = True,
    ) -> KnowledgeBase:
        """Create a validated knowledge base from FHIR terminology resources."""
        from lx_dtypes.models.knowledge_base.fhir.yaml import (
            knowledge_base_from_fhir,
        )

        return cast(
            "KnowledgeBase",
            knowledge_base_from_fhir(
                payload,
                module_name=module_name,
                version=version,
                medical_field=medical_field,
                author=author,
                language=language,
                strict=strict,
            ),
        )

    def export_terminology_validated_fhir_observations(
        self,
        reported_findings: Sequence[Mapping[str, object]],
        *,
        base_url: str = "https://wg-lux.de/fhir",
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        return export_terminology_validated_fhir_observations(
            reported_findings,
            findings=self.kb.finding,
            classifications=self.kb.classification,
            classification_choices=self.kb.classification_choice,
            units=self.kb.unit,
            base_url=base_url,
            language=language,
        )

    def import_terminology_validated_fhir_observations(
        self,
        observations: Sequence[Mapping[str, object]],
        *,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
        text_extractor: FindingTextExtractor | None = None,
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        return import_terminology_validated_fhir_observations(
            observations,
            findings=self.kb.finding,
            classifications=self.kb.classification,
            classification_choices=self.kb.classification_choice,
            units=self.kb.unit,
            language=language,
            text_extractor=text_extractor,
        )
