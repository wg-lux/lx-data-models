# Dates and Times

Owner: lx_dtypes maintainers. This guide owns shared timestamp and signed offset
contracts as well as date/time boundary conventions.

## Recording clock readings and offsets

Public imports from `lx_dtypes.models.contracts` include `PtsTimestamp`,
`ElectrosurgeryTimestamp`, `ExaminationTimestamp`, and `TimeOffset`.
PTS and electrosurgery readings retain signed integer `ticks` and a positive
rational time base: seconds equal `ticks * time_base_num / time_base_den`.
Examination readings require an aware `timestamp` and normalize it to UTC.
Their seconds are measured from the Unix epoch with microsecond precision.
Every reading requires a `clock_id`: identify the video generation, uninterrupted
generator clock epoch, or examination clock explicitly. Reuse the acquisition
clock identity when available; never reuse an identity after a clock reset.

`TimeOffset` records a `reference` and a `target` reading, each tagged with its
`kind` (`pts`, `electrosurgery`, or `examination`). Its `offset_seconds` property
is an exact `fractions.Fraction`, calculated as **target minus reference**.
Positive, zero, and negative offsets are supported. Persisted anchors retain
the full offset without storing a second value that could disagree with them.
When both readings observe the same event, add the offset to reference-clock
seconds to obtain target-clock seconds at that event.

```python
from pathlib import Path
from lx_dtypes.models.contracts import (
    ElectrosurgeryTimestamp, PtsTimestamp, TimeOffset,
)
from lx_dtypes.models.interface.data_formats import read_record, write_record

offset = TimeOffset(
    reference=PtsTimestamp(
        clock_id="video-generation-1", ticks=90000,
        time_base_num=1, time_base_den=90000,
    ),
    target=ElectrosurgeryTimestamp(
        clock_id="generator-epoch-1", ticks=1250,
        time_base_num=1, time_base_den=1000,
    ),
)
assert offset.offset_seconds.numerator == 1
assert offset.offset_seconds.denominator == 4  # +0.25 seconds
write_record(TimeOffset, offset, Path("offset.yml"))
assert read_record(TimeOffset, Path("offset.yml")) == offset
```

Use the same record API for examination anchors (`kind="examination"` with
`clock_id` and `timestamp`). See [record formats](record-data-formats.md) for
atomic file writes and supported formats. JSON serialization also round-trips
through `TimeOffset.model_validate_json(offset.model_dump_json())`.

A single offset records a relationship at its anchors; it does not establish
drift, verified frame ancestry, or safe extrapolation. Existing
`RecordingSynchronization` and
[electrosurgical video alignment](electrosurgical-video-alignment.md) retain
their multi-anchor and provenance requirements. Host applications own storage
locations and database persistence.

## Knowledge-base references and ledger observations

The ledger `p_time_offset` and `p_electrical_application` packages use the standard
`DataDict.py`, `Pydantic.py`, `Django.py`, and `__init__.py` layout. Existing imports
from either package remain valid. Django adapters load only when requested and
are registered by the packaged Django app; migration
`0008_electrical_and_time_observations` creates their tables. Evidence, curves, and
regression results are stored as JSON; examination and definition references
remain opaque strings. Parse through the Pydantic models and use the existing KB
validation methods for semantic checks before storage.

`models.knowledge_base.time_reference.TimeReference` is a standard KB record
(`model: time_reference`). It declares the reference and target clock kinds and
holds `TimeOffsetExample` entries, each with a unique `example_id`, a `role`
(`reference`, `training`, `validation`, or `test`), and validated evidence. The
parent definition's semantic name labels the time relationship. Examples are
optional; reusable definitions can be authored before training data is available.
Package examples must be synthetic or approved anonymized data without patient
identifiers, secrets, or local media paths. Roles are explicit author declarations;
the package neither creates splits nor verifies anonymization or permissions.

The executable example package's `config.yaml` selects this `.yml` file:

```{literalinclude} ../examples/dtypes_packages/time_references/references.yml
:language: yaml
```

`TimeOffsetEvidence` wraps a `TimeOffset` with `video_references`, keyed by its
PTS clock IDs. Each `TimeVideoReference` reuses the existing
`VideoSegmentTimelineCoordinates` contract, including its content hashes, exact
frame indices, rational time bases, and recording mapping status. An anchor must
match an exact first or last included frame's PTS and time base. A single-frame
segment can reference any exact frame. `timeline: recording` requires verified
original-recording coordinates; `generation` uses the referenced generation.
Missing and unused clock references, mismatched ticks, and conflicting clock
kinds or time bases are rejected. Generator and examination clocks do not need
invented video references.

`models.ledger.p_time_offset.PTimeOffset` inherits the ledger UUID, tags, creation
time, and external IDs. It stores `patient_examination`, `time_reference`, exact
`knowledge_base_module`/`knowledge_base_version`, and the same typed `evidence`.
`ddict`, `serialized_ddict`, YAML/JSON record persistence, and
`Ledger.time_offsets`/`export_record_lists()["p_time_offsets"]` retain all evidence.
KB loading, merging, record export (`time_references`), and complete package
snapshots retain examples and their roles. Empty time-reference families preserve
older snapshot digests; snapshots written before this family are still readable.
Older library releases cannot load packages containing the new record kind.

```python
from pathlib import Path
from lx_dtypes.packages import load_package
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset

kb = load_package(Path("docs/examples/dtypes_packages/time_references/config.yaml"))
reference = kb.time_reference["video_generator_event"]
# This demonstration reuses synthetic evidence, never a real patient identifier.
observation = PTimeOffset(
    patient_examination="synthetic-examination",
    time_reference=reference.name,
    knowledge_base_module=kb.config.name,
    knowledge_base_version=kb.config.version,
    evidence=reference.examples[0].evidence,
)
kb.validate_time_offset(observation)
```

`KnowledgeBase.validate_time_offset` resolves the semantic name and checks the
owning module's resolved version and both clock kinds. It also works with
references supplied by pinned package dependencies. It does not compare clock
origins between different acquisitions or infer drift from a training example.
For advisory feedback, `lx_dtypes.evaluation.assess_time_offset(kb, observation)`
applies those same rules and returns the shared `ValidationReport`.
The host must resolve the examination link and video hashes, verify that the
evidence belongs to that examination and acquisition, and authorize storage and
training use. Schema validation does not grant access to media or authorize
clinical use of a reference example.

Date and time fields must be strongly typed and timezone-aware at the model
boundary. Pydantic V2 provides the validation tools, but project code must reject
ambiguous values before they reach persistence or workflow logic.

## 1. Always Use Strong Typing

Never define a date field as a `str`, even if the input is a string from a JSON payload. Use Python’s standard library types. Pydantic will automatically parse ISO 8601 strings into these objects.

- **`datetime.date`**: For birthdays, holidays, or specific calendar days (no time component).
- **`datetime.datetime`**: For timestamps, log events, or scheduled appointments.
- **`datetime.time`**: For opening hours or recurring daily events.

## 2. Enforce Timezone Awareness

The most common bug in backend systems is mixing **Naive** (no timezone info) and **Aware** (timezone info included) datetimes.

Project rules:

- Store everything in **UTC**.
- Reject naive datetimes at the API boundary.
- Use Pydantic's `AwareDatetime` type (introduced in V2).

```python
from datetime import datetime, timezone
from pydantic import BaseModel, AwareDatetime

class Event(BaseModel):
    # Bad: accepts naive datetimes and defaults to local time.
    # created_at: datetime

    # Good: requires timezone information.
    start_time: AwareDatetime

# Usage
try:
    # Fails validation because no timezone is provided.
    Event(start_time=datetime(2023, 1, 1, 12, 0))
except ValueError:
    print("Validation Error: Timezone required")

# Passes validation.
Event(start_time=datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc))
```

## 3. Stick to ISO 8601 Standards

Pydantic is optimized to parse ISO 8601 formats (e.g., `YYYY-MM-DDTHH:MM:SSZ`).

- **Input:** Encourage clients to send ISO strings.
- **Output:** Pydantic serializes to ISO strings by default.
- **Avoid Custom Formats:** Avoid configuring Pydantic to parse format strings like `DD/MM/YYYY`. It makes your API brittle and region-dependent. If you *must* handle a legacy format, use a `BeforeValidator`.

## 4. Validate Business Logic

Use the `@field_validator` decorator to enforce logical constraints, such as ensuring a birth date is in the past or a scheduled task is in the future.

```python
from datetime import date
from pydantic import BaseModel, field_validator

class UserProfile(BaseModel):
    birth_date: date

    @field_validator('birth_date')
    @classmethod
    def must_be_18(cls, v: date) -> date:
        today = date.today()
        # Calculate age roughly
        age = (today - v).days / 365.25
        if age < 18:
            raise ValueError('User must be 18 or older')
        return v
```

## 5. Handle "Now" and Defaults

**Never** set a mutable default (like `datetime.now()`) directly in the field definition. Python evaluates default arguments once at definition time, not at instantiation time.

Bad:

```python
class Log(BaseModel):
    timestamp: datetime = datetime.now()  # Fixed at import time.
```

Good:

```python
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Log(BaseModel):
    # Evaluated every time a model is created.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

## 6. Serialization

When you convert your model to JSON (e.g., sending a response in FastAPI), Pydantic converts datetime objects to strings.

If you need a specific output format (that isn't standard ISO), strictly separate your **Internal Model** from your **Response Model**, or use a serialization serializer.

```python
from pydantic import BaseModel, field_serializer

class Meeting(BaseModel):
    when: datetime

    @field_serializer('when')
    def serialize_dt(self, dt: datetime, _info):
        # Custom format only for outgoing JSON
        return dt.strftime('%Y-%m-%d %H:%M')
```

## Summary Checklist

| Feature | Recommendation | Why? |
| --- | --- | --- |
| **Type** | `AwareDatetime` | Prevents timezone confusion. |
| **Defaults** | `Field(default_factory=...)` | Prevents stale timestamps. |
| **Validation** | `@field_validator` | Enforces logic (e.g., "date must be future"). |
| **Format** | ISO 8601 | Universal standard, reduces parsing errors. |
| **Storage** | UTC | Standardizes database entries. |

## 7. Complete Example

Here is a complete, production-ready example using Pydantic V2 features.

```python
from datetime import datetime, timezone
from pydantic import BaseModel, Field, AwareDatetime, field_validator

class Appointment(BaseModel):
    # Require timezone information.
    start_time: AwareDatetime

    # Use default_factory for creation times.
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    description: str

    # Apply business validation after parsing.
    @field_validator('start_time')
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        # Ensure the comparison is timezone-aware.
        if v < datetime.now(timezone.utc):
            raise ValueError('Appointment must be in the future')
        return v

# Valid input: ISO 8601 with timezone.
data = {
    "start_time": "2030-12-01T14:00:00Z",
    "description": "Dentist"
}
appt = Appointment(**data)
print(f"Success: {appt.start_time.isoformat()}")

# Invalid input: naive datetime.
try:
    Appointment(start_time=datetime(2030, 12, 1, 14, 0), description="Fail")
except Exception as e:
    print(f"\nCaught Expected Error: {e}")
```
