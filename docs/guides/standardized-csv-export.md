# Standardized CSV exports

Owner: lx_dtypes maintainers. This guide owns CSV projection of complete clinical
records and explicitly selected Django tables. Host authorization, database
transactions, and patient selection remain the host's responsibility.

## Ledger and knowledge base

`interface_tables` exports every `KnowledgeBase.export_record_lists()` and
`Ledger.export_record_lists()` collection, plus cases, the seven medical-ledger
record types, classification image annotations, and bounding-box annotations.
It retains new fields emitted by serialization, including fields not yet present
in a DataDict annotation. Empty collections produce header-only CSVs.

```python
from pathlib import Path
from lx_dtypes.stats.standardized import interface_tables, write_csv_tables

tables = interface_tables(
    db_interface,
    medical_ledgers=patient_medical_ledgers,
    image_annotations=dataset_export.frame_annotations,
    box_annotations=box_annotation_payloads,
)
write_csv_tables(tables, Path("standardized_dataset"), source="clinical_ledger",
                 overwrite=True)
```

Pass `PatientMedicalLedger` aggregates, `AIDataSetFrameAnnotationExport` records,
and `FrameBoxAnnotationBulkItemPayload` records respectively. These sources are
explicit because the examination `Ledger` does not own medical or image
collections. For a ledger without a KB, use `ledger_tables` with the same keyword
arguments. Existing EndoReg `build_patient_medical_ledger_for_patient` and dataset
export services supply the canonical medical and image records.

Medication columns include all current medication fields, substances, dosing,
periods, and BMP notes. Plans preserve ordered blocks and their medication UUID
references. Nested medications and lab values are included even when only reached
through a plan or sample. Identical repeated medical UUIDs deduplicate; conflicting
records with the same UUID fail. Annotation tables retain all fields of their
respective contracts. The bounding-box input contract does not carry timestamps;
use the database projection below to retain all persisted annotation metadata.

Patient videos reference their segments by UUID; `p_video_segments` and
`p_video_segment_states` carry each segment's frame range, label, label set,
timeline coordinates and annotation/validation state. A video's sensitive
metadata (names, birth date) is exported only as a UUID reference, never inline.

### Frames for AI training

`frames` lists each annotated frame once, joined to `image_annotations` and
`image_box_annotations` by `frame_id`. Its `export_path` column names where the
image is placed in the export, `frames/<video_uuid>/<relative_path>`. Pass the
images to the writer so the CSVs and frames are published together:

```python
from lx_dtypes.stats.standardized import frame_export_path

files = {
    frame_export_path(item.video_uuid, item.relative_path): Path(item.file_path)
    for item in dataset_export.frame_annotations
    if item.file_path
}
write_csv_tables(tables, Path("standardized_dataset"), source="ai_dataset",
                 overwrite=True, files=files)
```

Bundled files are copied, never linked; the manifest records each file's size and
SHA-256. Paths must be relative, without `..`, and may not end in `.csv`. A missing
source file aborts the export before anything is published.

## EndoReg and other Django databases

The generic adapter reads the current ORM schema, so newly added concrete fields
are exported without another handwritten field list. Pass explicitly selected
querysets from any configured database alias:

```python
from pathlib import Path
from endoreg_db.models import PatientMedication, PatientMedicationSchedule
from endoreg_db.models.label.annotation import ImageClassificationAnnotation, FrameBoxAnnotation
from lx_dtypes.django.standardized_export import export_querysets

export_querysets({
    "patient_medications": PatientMedication.objects.using(database_alias).filter(patient_id__in=patient_ids),
    "patient_medication_schedules": PatientMedicationSchedule.objects.using(database_alias).filter(patient_id__in=patient_ids),
    "image_annotations": ImageClassificationAnnotation.objects.using(database_alias).filter(frame_id__in=frame_ids),
    "image_box_annotations": FrameBoxAnnotation.objects.using(database_alias).filter(frame_id__in=frame_ids),
}, Path("standardized_dataset/endoreg"), overwrite=True)
```

Add querysets for examinations, findings, frames, labels, or other selected models
in the same mapping. The adapter applies the queryset's filters and database alias
and performs no database writes. Foreign keys use stored `*_id` columns. Forward
many-to-many relations produce `<table>__<relation>.csv`, including custom through
fields and only links belonging to selected source records. Referenced target
records are not automatically exported: include their querysets explicitly.
Sliced querysets are rejected; select IDs before export instead.

Rows follow the queryset's ordering, or primary-key order when it has none, so
repeated exports are byte-stable. A queryset filtered across a relation can repeat
a record (for example frames filtered by annotation label); such exports fail
until `.distinct()` is applied. Binary columns are rejected by default, because
EndoReg stores HLS encryption keys (`VideoHlsArtifact`) in them; pass
`binary="base64"` only for a selection that should contain binary data, such as
`VideoPredictionMeta.prediction_array`. File fields export their stored name.

To ship frame images with an EndoReg export, resolve each `Frame` to its file in
host code and pass `files=` exactly as for the ledger route; the adapter never
guesses storage locations.

Every EndoReg model (188 models, 68 many-to-many relations, all stock Django field
types) has been exported through this adapter against real tables; only the two
binary-field models above require the explicit opt-in.

The database projection preserves the host schema and local primary keys; it is
not a conversion to canonical ledger UUIDs. Use the host's existing clinical
adapters and the ledger route when a consumer requires canonical ledger semantics.
Use a host-managed consistent read transaction if an export must reflect one
snapshot while the database is changing. The implementation currently materializes
tables in memory before publishing.

## Encoding and regeneration

UTF-8 CSV uses standard quoting, ISO dates/timestamps, JSON for list/object cells,
and an empty cell for null (indistinguishable from an empty string). Boolean cells
are `true`/`false`. Unbounded KB limits use `Infinity`/`-Infinity`; NaN is rejected.
Pre-serialized ledger relationship strings retain their existing encoding.
`export_manifest.yml` lists the source label, column order, row counts and SHA-256
hashes. All CSVs are staged before publication; each file replacement is atomic,
but the whole directory is not a transaction. The manifest is published last.
Existing files require `overwrite=True`; unrelated files remain untouched.
The legacy Pandera dataset API and XLSX exports retain their existing scope.

To regenerate the local synthetic example with the complete CSV path:

```bash
uv run python scripts/usage_example.py --csv-output standardized_dataset
```

This command creates demo examination records and header-only medical/image tables;
it does not read an EndoReg database or invent medication/annotation observations.
For populated exports, supply those records through the APIs above.
