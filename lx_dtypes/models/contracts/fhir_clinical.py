from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Self, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FhirModel(BaseModel):
    """Small, lossless FHIR R4 contract base for fixture-driven validation."""

    model_config = ConfigDict(extra="allow")


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
    value: int | float
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class FhirObservationComponent(FhirModel):
    code: FhirCodeableConcept
    valueQuantity: FhirQuantity | None = None
    valueString: str | None = None
    valueBoolean: bool | None = None
    valueInteger: int | None = None
    valueDecimal: float | None = None
    valueCodeableConcept: FhirCodeableConcept | None = None

    @model_validator(mode="after")
    def validate_single_value(self) -> Self:
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
    id: str = Field(min_length=1)


class FhirObservation(FhirModel):
    resourceType: Literal["Observation"]
    id: str = Field(min_length=1)
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
    valueBoolean: bool | None = None
    valueInteger: int | None = None
    valueDecimal: float | None = None
    valueCodeableConcept: FhirCodeableConcept | None = None
    component: list[FhirObservationComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_value(self) -> Self:
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


class FhirCondition(FhirModel):
    resourceType: Literal["Condition"]
    id: str = Field(min_length=1)
    clinicalStatus: FhirCodeableConcept
    code: FhirCodeableConcept
    subject: FhirReference
    recordedDate: datetime | None = None


class FhirDiagnosticReport(FhirModel):
    resourceType: Literal["DiagnosticReport"]
    id: str = Field(min_length=1)
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
            for key in keys:
                if key in index and index[key] is not resource:
                    raise ValueError(f"Duplicate FHIR reference target {key!r}")
                index[key] = resource
        return index

    def resolve_reference(
        self,
        reference: FhirReference,
        expected_type: Type[ClinicalResourceT],
    ) -> ClinicalResourceT:
        resource = self.resource_index().get(reference.reference)
        if resource is None:
            raise ValueError(f"Unresolved FHIR reference {reference.reference!r}")
        if not isinstance(resource, expected_type):
            raise ValueError(
                f"FHIR reference {reference.reference!r} resolves to "
                f"{resource.resourceType}, expected {expected_type.__name__}"
            )
        return resource

    def validate_clinical_links(self) -> None:
        for entry in self.entry:
            resource = entry.resource
            if isinstance(resource, (FhirObservation, FhirCondition)):
                self.resolve_reference(resource.subject, FhirPatient)
            elif isinstance(resource, FhirDiagnosticReport):
                patient = self.resolve_reference(resource.subject, FhirPatient)
                for result in resource.result:
                    observation = self.resolve_reference(result, FhirObservation)
                    observation_patient = self.resolve_reference(
                        observation.subject,
                        FhirPatient,
                    )
                    if observation_patient.id != patient.id:
                        raise ValueError(
                            f"DiagnosticReport/{resource.id} and "
                            f"Observation/{observation.id} reference different patients"
                        )

    def resolved_reports(self) -> list[ResolvedDiagnosticReport]:
        self.validate_clinical_links()
        resolved: list[ResolvedDiagnosticReport] = []
        for entry in self.entry:
            report = entry.resource
            if not isinstance(report, FhirDiagnosticReport):
                continue
            patient = self.resolve_reference(report.subject, FhirPatient)
            observations = [
                self.resolve_reference(reference, FhirObservation)
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
