from __future__ import annotations

import builtins
from datetime import datetime
from typing import Annotated, Literal, Self, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

FhirId = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9.-]+$")]


class FhirModel(BaseModel):
    """Small, lossless FHIR R4 contract base for fixture-driven validation."""

    model_config = ConfigDict(
        extra="allow", allow_inf_nan=False, hide_input_in_errors=True
    )

    @model_validator(mode="after")
    def reject_unknown_modifiers(self) -> Self:
        extra = self.model_extra or {}
        if "modifierExtension" in extra or "implicitRules" in extra:
            raise ValueError(
                "FHIR modifiers and implicitRules require explicit profile support"
            )
        return self


class FhirCoding(FhirModel):
    system: str = Field(min_length=1)
    code: str = Field(min_length=1)
    display: str | None = None


class FhirCodeableConcept(FhirModel):
    coding: list[FhirCoding] = Field(min_length=1)
    text: str | None = None


class FhirReference(FhirModel):
    reference: str = Field(min_length=1)
    display: str | None = None


class FhirQuantity(FhirModel):
    value: Annotated[int, Field(strict=True)] | Annotated[float, Field(strict=True)]
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class FhirObservationComponent(FhirModel):
    code: FhirCodeableConcept
    valueQuantity: FhirQuantity | None = None
    valueString: str | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: Annotated[StrictInt, Field(ge=-(2**31), le=2**31 - 1)] | None = None
    valueDecimal: Annotated[float, Field(strict=True)] | None = None
    valueCodeableConcept: FhirCodeableConcept | None = None

    @model_validator(mode="after")
    def validate_single_value(self) -> Self:
        _reject_unrepresented_values(self)
        values = (
            self.valueQuantity,
            self.valueString,
            self.valueBoolean,
            self.valueInteger,
            self.valueDecimal,
            self.valueCodeableConcept,
        )
        if sum(value is not None for value in values) != 1:
            raise ValueError("Observation.component requires exactly one value[x]")
        return self


class FhirPatient(FhirModel):
    resourceType: Literal["Patient"]
    id: FhirId


class FhirObservation(FhirModel):
    resourceType: Literal["Observation"]
    id: FhirId
    status: Literal[
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ]
    code: FhirCodeableConcept
    subject: FhirReference
    effectiveDateTime: datetime | None = None
    valueQuantity: FhirQuantity | None = None
    valueString: str | None = None
    valueBoolean: StrictBool | None = None
    valueInteger: Annotated[StrictInt, Field(ge=-(2**31), le=2**31 - 1)] | None = None
    valueDecimal: Annotated[float, Field(strict=True)] | None = None
    valueCodeableConcept: FhirCodeableConcept | None = None
    component: list[FhirObservationComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_value(self) -> Self:
        _reject_unrepresented_values(self)
        values = (
            self.valueQuantity,
            self.valueString,
            self.valueBoolean,
            self.valueInteger,
            self.valueDecimal,
            self.valueCodeableConcept,
        )
        if sum(value is not None for value in values) > 1:
            raise ValueError("Observation permits at most one top-level value[x]")
        if not any(value is not None for value in values) and not self.component:
            raise ValueError("Observation requires a value[x] or component")
        return self


def _reject_unrepresented_values(model: FhirModel) -> None:
    # Retaining an unsupported choice as an extra field would bypass value[x]
    # cardinality checks and allow ambiguous clinical interpretation.
    if any(key.startswith("value") for key in (model.model_extra or {})):
        raise ValueError("Unsupported Observation value[x] in this clinical contract")
    if (model.model_extra or {}).get("dataAbsentReason") is not None:
        raise ValueError("dataAbsentReason requires a supported absent-result contract")


class FhirCondition(FhirModel):
    resourceType: Literal["Condition"]
    id: FhirId
    clinicalStatus: FhirCodeableConcept
    code: FhirCodeableConcept
    subject: FhirReference
    recordedDate: datetime | None = None


class FhirDiagnosticReport(FhirModel):
    resourceType: Literal["DiagnosticReport"]
    id: FhirId
    status: Literal[
        "registered",
        "partial",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "appended",
        "cancelled",
        "entered-in-error",
        "unknown",
    ]
    category: list[FhirCodeableConcept] = Field(default_factory=list)
    code: FhirCodeableConcept
    subject: FhirReference
    effectiveDateTime: datetime | None = None
    result: list[FhirReference] = Field(min_length=1)


ClinicalFhirResource = Annotated[
    FhirPatient | FhirObservation | FhirCondition | FhirDiagnosticReport,
    Field(discriminator="resourceType"),
]
ClinicalResourceT = TypeVar(
    "ClinicalResourceT",
    FhirPatient,
    FhirObservation,
    FhirCondition,
    FhirDiagnosticReport,
)


class FhirBundleRequest(FhirModel):
    method: Literal["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]
    url: str = Field(min_length=1)


class FhirClinicalBundleEntry(FhirModel):
    fullUrl: str | None = None
    resource: ClinicalFhirResource
    request: FhirBundleRequest | None = None


class ResolvedDiagnosticReport(BaseModel):
    patient: FhirPatient
    report: FhirDiagnosticReport
    observations: list[FhirObservation]


class FhirClinicalBundle(FhirModel):
    resourceType: Literal["Bundle"]
    type: Literal["collection", "transaction", "batch", "searchset"]
    entry: list[FhirClinicalBundleEntry] = Field(min_length=1)

    def resource_index(self) -> dict[str, ClinicalFhirResource]:
        index: dict[str, ClinicalFhirResource] = {}
        for entry in self.entry:
            resource = entry.resource
            keys = [f"{resource.resourceType}/{resource.id}"]
            if entry.fullUrl:
                keys.append(entry.fullUrl)
            for key in set(keys):
                if key in index:
                    raise ValueError("Duplicate FHIR reference target")
                index[key] = resource
        return index

    def resolve_reference(
        self,
        reference: FhirReference,
        expected_type: builtins.type[ClinicalResourceT],
    ) -> ClinicalResourceT:
        return self._resolve_reference(self.resource_index(), reference, expected_type)

    @staticmethod
    def _resolve_reference(
        index: dict[str, ClinicalFhirResource],
        reference: FhirReference,
        expected_type: builtins.type[ClinicalResourceT],
    ) -> ClinicalResourceT:
        resource = index.get(reference.reference)
        if resource is None:
            raise ValueError("Unresolved FHIR reference")
        if not isinstance(resource, expected_type):
            raise ValueError(  # noqa: TRY004 - invalid clinical reference target
                f"FHIR reference target has wrong type; expected {expected_type.__name__}"
            )
        return resource

    def validate_clinical_links(self) -> None:
        self._validate_clinical_links(self.resource_index())

    def _validate_clinical_links(self, index: dict[str, ClinicalFhirResource]) -> None:
        for entry in self.entry:
            resource = entry.resource
            if isinstance(resource, (FhirObservation, FhirCondition)):
                self._resolve_reference(index, resource.subject, FhirPatient)
            elif isinstance(resource, FhirDiagnosticReport):
                patient = self._resolve_reference(index, resource.subject, FhirPatient)
                for result in resource.result:
                    observation = self._resolve_reference(
                        index, result, FhirObservation
                    )
                    observation_patient = self._resolve_reference(
                        index,
                        observation.subject,
                        FhirPatient,
                    )
                    if observation_patient is not patient:
                        raise ValueError(
                            "DiagnosticReport and Observation reference different patients"
                        )

    def resolved_reports(self) -> list[ResolvedDiagnosticReport]:
        index = self.resource_index()
        self._validate_clinical_links(index)
        resolved: list[ResolvedDiagnosticReport] = []
        for entry in self.entry:
            report = entry.resource
            if not isinstance(report, FhirDiagnosticReport):
                continue
            patient = self._resolve_reference(index, report.subject, FhirPatient)
            observations = [
                self._resolve_reference(index, reference, FhirObservation)
                for reference in report.result
            ]
            resolved.append(
                ResolvedDiagnosticReport(
                    patient=patient,
                    report=report,
                    observations=observations,
                )
            )
        return resolved


__all__ = [
    "ClinicalFhirResource",
    "FhirClinicalBundle",
    "FhirClinicalBundleEntry",
    "FhirCodeableConcept",
    "FhirCoding",
    "FhirCondition",
    "FhirDiagnosticReport",
    "FhirObservation",
    "FhirObservationComponent",
    "FhirPatient",
    "FhirQuantity",
    "FhirReference",
    "ResolvedDiagnosticReport",
]
