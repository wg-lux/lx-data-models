# ePA FHIR compatibility

This guide defines what `lx_dtypes` contributes to exchange with the German
electronic patient record (ePA, "ePA für alle") and where the host takes over.
The ePA's only FHIR write interface for clinical content is the gematik
**ePA Medication Service**. This package targets its
[implementation guide 1.3.5](https://gemspec.gematik.de/ig/fhir/epa-medication/1.3.5/index.html)
(`de.gematik.epa.medication#1.3.5`, FHIR R4 4.0.1), with dosage following the
HL7 Deutschland medication profiles `DosageDgMP`/`TimingDgMP`
(`de.fhir.medication#1.0.7`).

## What the package provides

| Concern | Module | Contract |
|---|---|---|
| German identifier systems and check digits | `lx_dtypes.models.contracts.german_fhir` | `Kvnr` (KVNR, `http://fhir.de/sid/gkv/kvid-10`), `Pzn` (IFA modulo 11) and base-profile system URIs |
| KBV key tables bound by the profiles | `lx_dtypes.models.contracts.kbv_key_tables` | `S_BMP_DOSIEREINHEIT` V1.01 and `S_KBV_DARREICHUNGSFORM` V1.16 |
| Electronic medication plan (eMP) entries | `lx_dtypes.models.ledger.medical.epa` | `project_emp_entry()` returns eMP `Medication` and `MedicationRequest`; `$add-emp-entry` and `$update-emp-entry` Parameters builders |

`PatientMedication.pzn` rejects PZNs with an invalid check digit.

## Field mapping

| `PatientMedication` | eMP resource element |
|---|---|
| `pzn` | `Medication.code.coding:pzn` |
| `medication` | `Medication.code.text` |
| `substances[].name` / `.strength` | `Medication.ingredient.itemCodeableConcept.text` / `strength` `medication-ingredient-amount-extension` (kept verbatim) |
| `dosage_form_code` / `dosage_form` | `Medication.form.coding:kbvDarreichungsform` / `Medication.form.text` |
| `dosing` morning/noon/evening/night | `dosageInstruction.timing.repeat.when` `MORN`/`NOON`/`EVE`/`NIGHT`, one `Dosage` per distinct dose |
| `dosing.weekday` | `timing.repeat.dayOfWeek`, `periodUnit = wk` |
| `dosing.free_text` | a single text-only `dosageInstruction` |
| `unit_code` | `doseQuantity` in `KBV_CS_SFHIR_BMP_DOSIEREINHEIT` |
| `medication_indication` | `reason-patient-instruction-extension` |
| `notes`, `bound_note` | `patient-note-extension` (joined by a line break) |
| `start_at` / `end_at` | `effectiveDosePeriod` |
| `active` | `MedicationRequest.status = active` |

The host supplies an `EmpEntryContext`: the insurant's KVNR, `authoredOn`, an
explicit status for inactive entries, and an optional note for other providers
(`MedicationRequest.note`). Resource ids are deterministic UUIDv5 values derived
from the ledger entry UUID.

Structured dosing also emits `renderedDosageInstruction` (for example
`1-0-1-0 Stück`) and `GeneratedDosageInstructionsMeta`. The text comes from this
package's own renderer and is labelled `lx-dtypes-bmp-schema/1`, not the
HL7 Deutschland reference algorithm version. Hosts that run the reference
algorithm should replace both extensions before sending.

## Fail-closed rules

`project_emp_entry()` raises `EpaProjectionError` instead of guessing when:

- no trade name, PZN or active substance is present (`epa-med-1`);
- the dosage form code is not in the KBV Darreichungsform table;
- no dosage is recorded, because eMP requires `dosageInstruction`;
- structured dosing has no `unit_code`, because the dose unit binding is required;
- a dose such as `1/3` or `2/3` has no exact decimal value; record it as free text;
- legacy `dosage`/`intake_times` are populated, which would need clinical interpretation;
- an inactive entry has no explicit status, or the status contradicts `active`.

## Boundaries

- Transport, mutual TLS/VAU, authentication, the `acknowledgedChronologyId`
  handshake, and insurant consent belong to the host.
- The electronic medication list (eML) is filled by the e-prescription service
  and `$add-eml-entry` from dispensing or prescribing software; this package does
  not author eML entries.
- ePA documents (for example endoscopy reports as PDF/A with IHE XDS metadata)
  are not FHIR resources and are outside this guide.
- ICD-10-GM `reasonCode`, ATC/ASK codings, `Medication.amount` and package
  extensions are not projected because the ledger does not hold them.
- `MedicationScheduleHeading`, free-text lines and compounded-preparation rows of
  a BMP schedule have no eMP equivalent and are not projected.

## Validating against the official profiles

The unit tests check the resource shapes against the official gematik examples.
For conformance evidence, validate generated Parameters with the HL7 validator:

```bash
java -jar validator_cli.jar add_emp_entry.json \
  -version 4.0.1 -ig de.gematik.epa.medication#1.3.5
```

Run the tests with:

```bash
uv run pytest tests/unit/lx_dtypes/models/ledger/medical/test_epa_projection.py \
  tests/unit/lx_dtypes/models/contracts/test_german_fhir.py -q
```
