"""Project BMP-shaped patient medications onto the gematik ePA eMP write contract.

Targets ``de.gematik.epa.medication`` 1.3.5 (FHIR R4): an ``$add-emp-entry`` or
``$update-emp-entry`` Parameters resource carrying an eMP Medication and an eMP
MedicationRequest whose dosage follows HL7 Deutschland ``DosageDgMP``. The
projection fails closed instead of guessing: entries that cannot be represented
without loss or inference raise `EpaProjectionError`.

Transport, authentication, consent, and the ePA chronology handshake belong to
the host.
"""

from __future__ import annotations

import copy
import uuid
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Final, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.german_fhir import (
    IDENTIFIER_TYPE_DE_BASIS_SYSTEM,
    KBV_BMP_DOSIEREINHEIT_SYSTEM,
    KBV_DARREICHUNGSFORM_SYSTEM,
    KVID_10_SYSTEM,
    PZN_SYSTEM,
    Kvnr,
)
from lx_dtypes.models.contracts.json_types import JsonObject, JsonValue
from lx_dtypes.models.contracts.kbv_key_tables import (
    BMP_DOSIEREINHEIT,
    KBV_DARREICHUNGSFORM,
)
from lx_dtypes.models.contracts.medication import MedicationDosingSchedule

from .Pydantic import PatientMedication

EPA_MEDICATION_IG_VERSION: Final = "1.3.5"
EPA_MEDICATION_CANONICAL: Final = "https://gematik.de/fhir/epa-medication"
EMP_MEDICATION_PROFILE: Final = (
    f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/emp-medication"
)
EMP_MEDICATION_REQUEST_PROFILE: Final = (
    f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/emp-medication-request"
)
ADD_EMP_ENTRY_PARAMETERS_PROFILE: Final = f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/epa-op-add-emp-entry-input-parameters"
UPDATE_EMP_ENTRY_PARAMETERS_PROFILE: Final = f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/epa-op-update-emp-entry-input-parameters"
EMP_IDENTIFIER_SYSTEM: Final = "https://gematik.de/fhir/sid/emp-identifier"

_CONTEXT_EXTENSION: Final = (
    f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/context-extension"
)
_REASON_PATIENT_INSTRUCTION_EXTENSION: Final = f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/reason-patient-instruction-extension"
_PATIENT_NOTE_EXTENSION: Final = (
    f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/patient-note-extension"
)
_INGREDIENT_AMOUNT_EXTENSION: Final = f"{EPA_MEDICATION_CANONICAL}/StructureDefinition/medication-ingredient-amount-extension"
_EFFECTIVE_DOSE_PERIOD_EXTENSION: Final = "http://hl7.org/fhir/5.0/StructureDefinition/extension-MedicationRequest.effectiveDosePeriod"
_RENDERED_DOSAGE_EXTENSION: Final = (
    "http://hl7.org/fhir/5.0/StructureDefinition/"
    "extension-MedicationRequest.renderedDosageInstruction"
)
_GENERATED_DOSAGE_META_EXTENSION: Final = "http://ig.fhir.de/igs/medication/StructureDefinition/GeneratedDosageInstructionsMeta"

# Identifies this module's renderer; it is not the HL7 Deutschland reference algorithm.
DOSAGE_TEXT_ALGORITHM_VERSION: Final = "lx-dtypes-bmp-schema/1"

_EVENT_TIMING: Final = (
    ("morning", "MORN"),
    ("noon", "NOON"),
    ("evening", "EVE"),
    ("night", "NIGHT"),
)
# BMP weekday 1..7 is Monday..Sunday (bmp_V2.8.xsd ``wochentagTyp``).
_DAY_OF_WEEK: Final = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_WEEKDAY_LABEL_DE: Final = (
    "montags",
    "dienstags",
    "mittwochs",
    "donnerstags",
    "freitags",
    "samstags",
    "sonntags",
)
_ID_NAMESPACE: Final = uuid.UUID("5b1f7c1e-6f53-4a8e-9a39-0c5e1f0d6a21")

EmpMedicationRequestStatus = Literal[
    "active", "on-hold", "completed", "stopped", "entered-in-error"
]


class EpaProjectionError(ValueError):
    """The medication entry cannot be represented in the eMP without loss or inference."""


class EmpEntryContext(BaseModel):
    """Host-supplied facts the ledger entry does not carry."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    kvnr: Kvnr
    authored_on: date | AwareDatetime
    status: EmpMedicationRequestStatus | None = Field(
        default=None,
        description="Required when the entry is inactive; never inferred from dates.",
    )
    provider_note: str | None = Field(default=None, min_length=1)


class EmpEntryProjection(BaseModel):
    """eMP Medication and MedicationRequest resources for one ledger entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    medication: JsonObject
    medication_request: JsonObject

    def add_emp_entry_parameters(
        self, acknowledged_chronology_id: str | None = None
    ) -> JsonObject:
        """Build the ``$add-emp-entry`` input Parameters with the Medication inline."""

        parameters: list[JsonValue] = []
        if acknowledged_chronology_id is not None:
            parameters.append(
                {
                    "name": "acknowledgedChronologyId",
                    "valueId": acknowledged_chronology_id,
                }
            )
        parameters.append(
            {
                "name": "medication",
                "part": [
                    {"name": "resource", "resource": copy.deepcopy(self.medication)}
                ],
            }
        )
        parameters.append(
            {"name": "empEntry", "resource": copy.deepcopy(self.medication_request)}
        )
        return {
            "resourceType": "Parameters",
            "meta": {"profile": [ADD_EMP_ENTRY_PARAMETERS_PROFILE]},
            "parameter": parameters,
        }

    def update_emp_entry_parameters(
        self,
        *,
        medication_plan_identifier: str,
        medication_reference: str,
        acknowledged_chronology_id: str | None = None,
    ) -> JsonObject:
        """Build ``$update-emp-entry`` Parameters for an entry the ePA already holds.

        ``medication_plan_identifier`` and ``medication_reference`` are the
        server-assigned eMP identifier and ``Medication/<id>`` of the existing entry.
        """

        if not medication_plan_identifier:
            raise EpaProjectionError("medication_plan_identifier must not be empty")
        if not medication_reference.startswith("Medication/") or "/_history/" in (
            medication_reference
        ):
            raise EpaProjectionError(
                "medication_reference must be a non-versioned Medication/<id> reference"
            )
        request = copy.deepcopy(self.medication_request)
        request["identifier"] = [
            {"system": EMP_IDENTIFIER_SYSTEM, "value": medication_plan_identifier}
        ]
        request["medicationReference"] = {"reference": medication_reference}
        parameters: list[JsonValue] = []
        if acknowledged_chronology_id is not None:
            parameters.append(
                {
                    "name": "acknowledgedChronologyId",
                    "valueId": acknowledged_chronology_id,
                }
            )
        parameters.append(
            {
                "name": "medicationPlanIdentifier",
                "valueIdentifier": {
                    "system": EMP_IDENTIFIER_SYSTEM,
                    "value": medication_plan_identifier,
                },
            }
        )
        parameters.append({"name": "empEntry", "resource": request})
        return {
            "resourceType": "Parameters",
            "meta": {"profile": [UPDATE_EMP_ENTRY_PARAMETERS_PROFILE]},
            "parameter": parameters,
        }


def project_emp_entry(
    medication: PatientMedication, context: EmpEntryContext
) -> EmpEntryProjection:
    """Project one ledger medication onto eMP Medication and MedicationRequest."""

    medication_id = _fhir_id(medication, "emp-medication")
    return EmpEntryProjection(
        medication=_emp_medication(medication, medication_id),
        medication_request=_emp_medication_request(medication, context, medication_id),
    )


def _fhir_id(medication: PatientMedication, role: str) -> str:
    return str(uuid.uuid5(_ID_NAMESPACE, f"{medication.uuid}/{role}"))


def _emp_medication(medication: PatientMedication, medication_id: str) -> JsonObject:
    if (
        medication.medication is None
        and medication.pzn is None
        and not medication.substances
    ):
        # epa-med-1: code or ingredient must exist.
        raise EpaProjectionError(
            "an eMP medication requires a trade name, PZN, or active substance"
        )
    resource: JsonObject = {
        "resourceType": "Medication",
        "id": medication_id,
        "meta": {"profile": [EMP_MEDICATION_PROFILE]},
        "extension": [{"url": _CONTEXT_EXTENSION, "valueCode": "EMP"}],
        "status": "active",
    }
    code: JsonObject = {}
    if medication.pzn is not None:
        code["coding"] = [{"system": PZN_SYSTEM, "code": medication.pzn}]
    if medication.medication is not None:
        code["text"] = medication.medication
    if code:
        resource["code"] = code
    form = _form(medication)
    if form is not None:
        resource["form"] = form
    if medication.substances:
        ingredients: list[JsonValue] = []
        for substance in medication.substances:
            ingredient: JsonObject = {
                "itemCodeableConcept": {"text": substance.name},
                "isActive": True,
            }
            if substance.strength is not None:
                # BMP strength is display text; the eMP keeps it verbatim instead of a parsed Ratio.
                ingredient["strength"] = {
                    "extension": [
                        {
                            "url": _INGREDIENT_AMOUNT_EXTENSION,
                            "valueString": substance.strength,
                        }
                    ]
                }
            ingredients.append(ingredient)
        resource["ingredient"] = ingredients
    return resource


def _form(medication: PatientMedication) -> JsonObject | None:
    if medication.dosage_form_code is not None:
        display = KBV_DARREICHUNGSFORM.get(medication.dosage_form_code)
        if display is None:
            raise EpaProjectionError(
                f"dosage form code {medication.dosage_form_code!r} is not in the KBV "
                "Darreichungsform key table"
            )
        return {
            "coding": [
                {
                    "system": KBV_DARREICHUNGSFORM_SYSTEM,
                    "code": medication.dosage_form_code,
                    "display": display,
                }
            ]
        }
    if medication.dosage_form is not None:
        return {"text": medication.dosage_form}
    return None


def _emp_medication_request(
    medication: PatientMedication, context: EmpEntryContext, medication_id: str
) -> JsonObject:
    status = context.status
    if status is None:
        if not medication.active:
            raise EpaProjectionError(
                "inactive entries require an explicit eMP status; it is not inferred"
            )
        status = "active"
    elif status == "active" and not medication.active:
        raise EpaProjectionError("status 'active' contradicts an inactive entry")

    extensions: list[JsonValue] = [{"url": _CONTEXT_EXTENSION, "valueCode": "EMP"}]
    if medication.medication_indication is not None:
        extensions.append(
            {
                "url": _REASON_PATIENT_INSTRUCTION_EXTENSION,
                "valueString": medication.medication_indication,
            }
        )
    patient_note = "\n".join(
        note for note in (medication.notes, medication.bound_note) if note is not None
    )
    if patient_note:
        extensions.append(
            {"url": _PATIENT_NOTE_EXTENSION, "valueAnnotation": {"text": patient_note}}
        )
    if medication.start_at is not None:
        period: JsonObject = {"start": _datetime(medication.start_at)}
        if medication.end_at is not None:
            period["end"] = _datetime(medication.end_at)
        extensions.append(
            {"url": _EFFECTIVE_DOSE_PERIOD_EXTENSION, "valuePeriod": period}
        )

    dosage, rendered = _dosage(medication)
    if rendered is not None:
        extensions.append(
            {"url": _RENDERED_DOSAGE_EXTENSION, "valueMarkdown": rendered}
        )
        extensions.append(
            {
                "url": _GENERATED_DOSAGE_META_EXTENSION,
                "extension": [
                    {"url": "language", "valueCode": "de-DE"},
                    {
                        "url": "algorithmVersion",
                        "valueString": DOSAGE_TEXT_ALGORITHM_VERSION,
                    },
                ],
            }
        )

    resource: JsonObject = {
        "resourceType": "MedicationRequest",
        "id": _fhir_id(medication, "emp-medication-request"),
        "meta": {"profile": [EMP_MEDICATION_REQUEST_PROFILE]},
        "extension": extensions,
        "status": status,
        "intent": "plan",
        "medicationReference": {"reference": f"Medication/{medication_id}"},
        "subject": {
            "identifier": {
                "type": {
                    "coding": [
                        {"system": IDENTIFIER_TYPE_DE_BASIS_SYSTEM, "code": "KVZ10"}
                    ]
                },
                "system": KVID_10_SYSTEM,
                "value": context.kvnr,
            }
        },
        "authoredOn": _datetime(context.authored_on),
        "dosageInstruction": dosage,
    }
    if context.provider_note is not None:
        resource["note"] = [{"text": context.provider_note}]
    return resource


def _datetime(value: date | datetime) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return value.isoformat()


def _dosage(medication: PatientMedication) -> tuple[list[JsonValue], str | None]:
    """Return DosageDgMP elements and, for structured dosing, the rendered text."""

    if medication.dosage is not None or medication.intake_times:
        raise EpaProjectionError(
            "legacy dosage/intake_times cannot be projected without clinical "
            "interpretation; record BMP dosing instead"
        )
    dosing = medication.dosing
    if dosing.free_text is not None:
        # DosageStructuredOrFreeText / FreeTextSingleDosageOnly: exactly one text-only Dosage.
        return [{"text": dosing.free_text}], None
    if dosing.is_empty():
        raise EpaProjectionError("an eMP entry requires a dosage instruction")
    if medication.unit_code is None:
        raise EpaProjectionError(
            "structured eMP dosing requires a KBV Dosiereinheit unit_code; "
            "a free-text unit cannot satisfy the required binding"
        )
    unit_display = BMP_DOSIEREINHEIT[medication.unit_code]

    # TimingSingleDosageForWhen: one Dosage per distinct dose value.
    groups: dict[Decimal, list[JsonValue]] = {}
    for field_name, when in _EVENT_TIMING:
        slot = getattr(dosing, field_name)
        if slot is not None:
            groups.setdefault(_slot_value(slot), []).append(when)

    repeat_base: JsonObject = {"period": 1}
    if dosing.weekday is not None:
        repeat_base["dayOfWeek"] = [_DAY_OF_WEEK[dosing.weekday - 1]]
        repeat_base["periodUnit"] = "wk"
    else:
        repeat_base["periodUnit"] = "d"

    dosages: list[JsonValue] = []
    for value, whens in groups.items():
        dosages.append(
            {
                "timing": {
                    "repeat": {
                        # TimingFrequencyCount: one administration per when (per weekday).
                        "frequency": len(whens),
                        **repeat_base,
                        "when": whens,
                    }
                },
                "doseAndRate": [
                    {
                        "doseQuantity": {
                            "value": _json_number(value),
                            "unit": unit_display,
                            "system": KBV_BMP_DOSIEREINHEIT_SYSTEM,
                            "code": medication.unit_code,
                        }
                    }
                ],
            }
        )
    return dosages, _render_schema(dosing, unit_display)


def _slot_value(slot: str) -> Decimal:
    if "/" in slot:
        fraction = Fraction(slot)
        value = Decimal(fraction.numerator) / Decimal(fraction.denominator)
        if Fraction(value) != fraction:
            raise EpaProjectionError(
                f"dose {slot!r} has no exact decimal value; record it as free-text dosing"
            )
        return value
    return Decimal(slot.replace(",", "."))


def _json_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _render_schema(dosing: MedicationDosingSchedule, unit_display: str) -> str:
    schema = "-".join(
        getattr(dosing, field_name) or "0" for field_name, _ in _EVENT_TIMING
    )
    text = f"{schema} {unit_display}"
    if dosing.weekday is not None:
        return f"{_WEEKDAY_LABEL_DE[dosing.weekday - 1]}: {text}"
    return text


__all__ = [
    "ADD_EMP_ENTRY_PARAMETERS_PROFILE",
    "DOSAGE_TEXT_ALGORITHM_VERSION",
    "EMP_IDENTIFIER_SYSTEM",
    "EMP_MEDICATION_PROFILE",
    "EMP_MEDICATION_REQUEST_PROFILE",
    "EPA_MEDICATION_CANONICAL",
    "EPA_MEDICATION_IG_VERSION",
    "UPDATE_EMP_ENTRY_PARAMETERS_PROFILE",
    "EmpEntryContext",
    "EmpEntryProjection",
    "EmpMedicationRequestStatus",
    "EpaProjectionError",
    "project_emp_entry",
]
