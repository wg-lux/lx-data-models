"""Media workflow state and transition contract shared by every layer.

One imported video or report moves through three tracks: a privacy track that
ends with the raw media purged, an annotation track that starts once processed
media exist, and a release track that joins both. This module only declares
state, event and transition tokens plus the invariants of the table; the pure
reducer lives in the Rust engine and persistence in endoreg-db. Tokens equal the
wire tokens of ``endoreg_db.services.clinical_lifecycle`` so both stay parity
testable.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PrivacyStage(StrEnum):
    IMPORT_PENDING = "import_pending"
    IMPORTING = "importing"
    QUARANTINED = "quarantined"
    AWAITING_VALIDATION = "awaiting_validation"
    VALIDATED = "validated"
    RAW_PURGED = "raw_purged"
    FAILED = "failed"
    LOST = "lost"
    WITHDRAWN = "withdrawn"


class AnnotationStage(StrEnum):
    NOT_AVAILABLE = "not_available"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"


class ReleaseStage(StrEnum):
    NOT_RELEASED = "not_released"
    EXPORT_READY = "export_ready"
    EXPORTED = "exported"
    DATASET_INGESTED = "dataset_ingested"


class WorkflowEvent(StrEnum):
    IMPORT_STARTED = "import_started"
    QUARANTINED = "quarantined"
    QUARANTINE_RELEASED = "quarantine_released"
    ARTIFACT_PUBLISHED = "artifact_published"
    CORRECTION_REQUESTED = "correction_requested"
    ANONYMIZATION_VALIDATED = "anonymization_validated"
    RAW_PURGED = "raw_purged"
    PROCESSING_FAILED = "processing_failed"
    INTEGRITY_LOST = "integrity_lost"
    RETRY_REQUESTED = "retry_requested"
    RECONCILE_RETRY = "reconcile_retry"
    RECONCILE_FAIL = "reconcile_fail"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    ANNOTATION_COMPLETED = "annotation_completed"
    ANNOTATION_REOPENED = "annotation_reopened"
    EXPORT_APPROVED = "export_approved"
    EXPORT_REVOKED = "export_revoked"
    EXPORTED = "exported"
    DATASET_INGESTED = "dataset_ingested"


class GdprDeletionPoint(StrEnum):
    """The only transitions that may delete data; nothing else deletes."""

    RAW_AND_IDENTIFIERS = "raw_and_identifiers"
    TRANSFER_STAGING = "transfer_staging"
    ALL_ARTIFACTS = "all_artifacts"


_P = PrivacyStage
_A = AnnotationStage
_R = ReleaseStage
_E = WorkflowEvent

PRIVACY_INACTIVE: Final = frozenset({_P.FAILED, _P.LOST, _P.WITHDRAWN})
PRIVACY_ACTIVE: Final = tuple(stage for stage in _P if stage not in PRIVACY_INACTIVE)

# event -> {source stage: target stage}; self-transitions make redelivery idempotent.
PRIVACY_TRANSITIONS: Final[Mapping[_E, Mapping[_P, _P]]] = MappingProxyType(
    {
        _E.IMPORT_STARTED: {
            _P.IMPORT_PENDING: _P.IMPORTING,
            _P.IMPORTING: _P.IMPORTING,
        },
        _E.QUARANTINED: {_P.IMPORTING: _P.QUARANTINED, _P.QUARANTINED: _P.QUARANTINED},
        _E.QUARANTINE_RELEASED: {_P.QUARANTINED: _P.IMPORTING},
        _E.ARTIFACT_PUBLISHED: {
            _P.IMPORTING: _P.AWAITING_VALIDATION,
            _P.AWAITING_VALIDATION: _P.AWAITING_VALIDATION,
        },
        # Only before validation; validation is final.
        _E.CORRECTION_REQUESTED: {_P.AWAITING_VALIDATION: _P.IMPORTING},
        _E.ANONYMIZATION_VALIDATED: {
            _P.AWAITING_VALIDATION: _P.VALIDATED,
            _P.VALIDATED: _P.VALIDATED,
        },
        _E.RAW_PURGED: {_P.VALIDATED: _P.RAW_PURGED, _P.RAW_PURGED: _P.RAW_PURGED},
        _E.PROCESSING_FAILED: {
            **{stage: _P.FAILED for stage in PRIVACY_ACTIVE},
            _P.FAILED: _P.FAILED,
        },
        _E.INTEGRITY_LOST: {
            **{stage: _P.LOST for stage in PRIVACY_ACTIVE},
            _P.FAILED: _P.LOST,
            _P.LOST: _P.LOST,
        },
        _E.RETRY_REQUESTED: {_P.FAILED: _P.IMPORT_PENDING},
        _E.RECONCILE_RETRY: {_P.LOST: _P.IMPORT_PENDING},
        _E.RECONCILE_FAIL: {_P.LOST: _P.FAILED},
        _E.CONSENT_WITHDRAWN: {stage: _P.WITHDRAWN for stage in _P},
    }
)

ANNOTATION_TRANSITIONS: Final[Mapping[_E, Mapping[_A, _A]]] = MappingProxyType(
    {
        _E.ANNOTATION_COMPLETED: {
            _A.IN_PROGRESS: _A.VALIDATED,
            _A.VALIDATED: _A.VALIDATED,
        },
        _E.ANNOTATION_REOPENED: {
            _A.IN_PROGRESS: _A.IN_PROGRESS,
            _A.VALIDATED: _A.IN_PROGRESS,
        },
    }
)

RELEASE_TRANSITIONS: Final[Mapping[_E, Mapping[_R, _R]]] = MappingProxyType(
    {
        _E.EXPORT_APPROVED: {
            _R.NOT_RELEASED: _R.EXPORT_READY,
            _R.EXPORT_READY: _R.EXPORT_READY,
        },
        _E.EXPORT_REVOKED: {
            _R.EXPORT_READY: _R.NOT_RELEASED,
            _R.NOT_RELEASED: _R.NOT_RELEASED,
        },
        _E.EXPORTED: {_R.EXPORT_READY: _R.EXPORTED, _R.EXPORTED: _R.EXPORTED},
        _E.DATASET_INGESTED: {
            _R.EXPORT_READY: _R.DATASET_INGESTED,
            _R.EXPORTED: _R.DATASET_INGESTED,
            _R.DATASET_INGESTED: _R.DATASET_INGESTED,
        },
    }
)

# Event that performs each deletion; the reducer must reject deletion elsewhere.
GDPR_DELETION_EVENTS: Final[Mapping[GdprDeletionPoint, _E]] = MappingProxyType(
    {
        GdprDeletionPoint.RAW_AND_IDENTIFIERS: _E.RAW_PURGED,
        GdprDeletionPoint.TRANSFER_STAGING: _E.EXPORTED,
        GdprDeletionPoint.ALL_ARTIFACTS: _E.CONSENT_WITHDRAWN,
    }
)


def event_track_tables() -> tuple[
    Mapping[_E, Mapping[_P, _P]],
    Mapping[_E, Mapping[_A, _A]],
    Mapping[_E, Mapping[_R, _R]],
]:
    return PRIVACY_TRANSITIONS, ANNOTATION_TRANSITIONS, RELEASE_TRANSITIONS


class MediaKind(StrEnum):
    VIDEO = "video"
    REPORT = "report"


class ExportApproval(StrEnum):
    NONE = "none"
    CURRENT = "current"
    # Approval exists but is bound to another processed-artifact generation.
    STALE = "stale"


class TransitionRejection(StrEnum):
    EVENT_NOT_PERMITTED_IN_STATE = "event_not_permitted_in_state"
    RECORD_INACTIVE = "record_inactive"
    VALIDATION_IS_FINAL = "validation_is_final"
    IDENTITY_NOT_VERIFIED = "identity_not_verified"
    PRIVACY_TRACK_INCOMPLETE = "privacy_track_incomplete"
    ANNOTATION_TRACK_INCOMPLETE = "annotation_track_incomplete"
    ALREADY_RELEASED = "already_released"


class EventOrigin(StrEnum):
    """Who may post an event; system events are never accepted from an API client."""

    USER = "user"
    SYSTEM = "system"


_ORIGIN_USER = EventOrigin.USER
_ORIGIN_SYSTEM = EventOrigin.SYSTEM

# Token classification only; guards and roles stay in the reducer and authz.
EVENT_ORIGINS: Final[Mapping[_E, EventOrigin]] = MappingProxyType(
    {
        _E.IMPORT_STARTED: _ORIGIN_SYSTEM,
        _E.QUARANTINED: _ORIGIN_SYSTEM,
        _E.QUARANTINE_RELEASED: _ORIGIN_USER,
        _E.ARTIFACT_PUBLISHED: _ORIGIN_SYSTEM,
        _E.CORRECTION_REQUESTED: _ORIGIN_USER,
        _E.ANONYMIZATION_VALIDATED: _ORIGIN_USER,
        _E.RAW_PURGED: _ORIGIN_SYSTEM,
        _E.PROCESSING_FAILED: _ORIGIN_SYSTEM,
        _E.INTEGRITY_LOST: _ORIGIN_SYSTEM,
        _E.RETRY_REQUESTED: _ORIGIN_USER,
        _E.RECONCILE_RETRY: _ORIGIN_USER,
        _E.RECONCILE_FAIL: _ORIGIN_USER,
        _E.CONSENT_WITHDRAWN: _ORIGIN_USER,
        _E.ANNOTATION_COMPLETED: _ORIGIN_USER,
        _E.ANNOTATION_REOPENED: _ORIGIN_USER,
        _E.EXPORT_APPROVED: _ORIGIN_USER,
        _E.EXPORT_REVOKED: _ORIGIN_USER,
        _E.EXPORTED: _ORIGIN_SYSTEM,
        _E.DATASET_INGESTED: _ORIGIN_SYSTEM,
    }
)


class WorklistStage(StrEnum):
    VALIDATE = "validate"
    ANNOTATE = "annotate"
    APPROVE_EXPORT = "approve_export"


class MediaWorkflowState(BaseModel):
    """Persisted state of one media item; ``version`` is the compare-and-swap token."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    privacy: PrivacyStage
    annotation: AnnotationStage
    release: ReleaseStage
    version: int = Field(ge=0)


class MediaWorkflowTransitionRequest(BaseModel):
    """Transition command; the actor comes from the authenticated session, never the body."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event: WorkflowEvent
    expected_version: int = Field(ge=0)
    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def only_user_events(self) -> Self:
        if EVENT_ORIGINS[self.event] is not EventOrigin.USER:
            raise ValueError("System events cannot be posted by a client")
        return self


def validate_transition_tables() -> None:
    """Raise when the declarative tables violate the contract invariants."""
    privacy, annotation, release = event_track_tables()
    event_tracks = [set(privacy), set(annotation), set(release)]
    if sum(len(tracks) for tracks in event_tracks) != len(set().union(*event_tracks)):
        raise ValueError("An event may belong to exactly one track")
    if set().union(*event_tracks) != set(WorkflowEvent):
        raise ValueError("Every event must belong to a track")
    if set(EVENT_ORIGINS) != set(WorkflowEvent):
        raise ValueError("Every event needs an origin")
    if set(GDPR_DELETION_EVENTS) != set(GdprDeletionPoint):
        raise ValueError("Every deletion point needs exactly one event")
    for sources in privacy.values():
        for source, target in sources.items():
            if (
                source is PrivacyStage.WITHDRAWN
                and target is not PrivacyStage.WITHDRAWN
            ):
                raise ValueError("Withdrawn is terminal")
    if _E.CORRECTION_REQUESTED in privacy and set(privacy[_E.CORRECTION_REQUESTED]) != {
        PrivacyStage.AWAITING_VALIDATION
    }:
        raise ValueError("Correction is only possible before validation")
