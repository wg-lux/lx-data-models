import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.media_workflow import (
    ANNOTATION_TRANSITIONS,
    EVENT_ORIGINS,
    GDPR_DELETION_EVENTS,
    PRIVACY_TRANSITIONS,
    RELEASE_TRANSITIONS,
    AnnotationStage,
    GdprDeletionPoint,
    MediaWorkflowState,
    MediaWorkflowTransitionRequest,
    PrivacyStage,
    ReleaseStage,
    WorkflowEvent,
    validate_transition_tables,
)


def test_transition_tables_satisfy_contract() -> None:
    validate_transition_tables()


def test_every_event_belongs_to_exactly_one_track() -> None:
    tracks = [
        set(PRIVACY_TRANSITIONS),
        set(ANNOTATION_TRANSITIONS),
        set(RELEASE_TRANSITIONS),
    ]
    assert set().union(*tracks) == set(WorkflowEvent)
    assert sum(len(track) for track in tracks) == len(WorkflowEvent)


@pytest.mark.parametrize("stage", list(PrivacyStage))
def test_consent_withdrawal_is_possible_from_every_stage(stage: PrivacyStage) -> None:
    assert (
        PRIVACY_TRANSITIONS[WorkflowEvent.CONSENT_WITHDRAWN][stage]
        is PrivacyStage.WITHDRAWN
    )


@pytest.mark.parametrize("stage", [PrivacyStage.VALIDATED, PrivacyStage.RAW_PURGED])
def test_no_correction_after_validation(stage: PrivacyStage) -> None:
    assert stage not in PRIVACY_TRANSITIONS[WorkflowEvent.CORRECTION_REQUESTED]


def test_lost_only_exits_through_reconcile_or_withdrawal() -> None:
    exits = {
        event
        for event, sources in PRIVACY_TRANSITIONS.items()
        if sources.get(PrivacyStage.LOST, PrivacyStage.LOST) is not PrivacyStage.LOST
    }
    assert exits == {
        WorkflowEvent.RECONCILE_RETRY,
        WorkflowEvent.RECONCILE_FAIL,
        WorkflowEvent.CONSENT_WITHDRAWN,
    }


def test_deletion_points_map_to_distinct_events() -> None:
    assert set(GDPR_DELETION_EVENTS) == set(GdprDeletionPoint)
    assert len(set(GDPR_DELETION_EVENTS.values())) == len(GdprDeletionPoint)


def test_state_uses_wire_field_names() -> None:
    state = MediaWorkflowState(
        privacy=PrivacyStage.RAW_PURGED,
        annotation=AnnotationStage.VALIDATED,
        release=ReleaseStage.EXPORT_READY,
        version=7,
    )
    assert state.version == 7


@pytest.mark.parametrize(
    "payload",
    [
        {
            "event": "exported",
            "expected_version": -1,
            "idempotency_key": "key-12345",
        },
        {
            "event": "exported",
            "expected_version": 1,
            "idempotency_key": "short",
        },
        {
            "event": "unknown",
            "expected_version": 1,
            "idempotency_key": "key-12345",
        },
    ],
)
def test_invalid_transition_requests_are_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        MediaWorkflowTransitionRequest.model_validate(payload)


def test_every_event_has_an_origin() -> None:
    assert set(EVENT_ORIGINS) == set(WorkflowEvent)


@pytest.mark.parametrize(
    "event",
    [
        WorkflowEvent.RAW_PURGED,
        WorkflowEvent.ARTIFACT_PUBLISHED,
        WorkflowEvent.INTEGRITY_LOST,
        WorkflowEvent.EXPORTED,
    ],
)
def test_system_events_are_not_postable(event: WorkflowEvent) -> None:
    with pytest.raises(ValidationError, match="System events"):
        MediaWorkflowTransitionRequest(
            event=event, expected_version=1, idempotency_key="key-12345"
        )


def test_client_cannot_supply_actor() -> None:
    with pytest.raises(ValidationError):
        MediaWorkflowTransitionRequest.model_validate(
            {
                "event": "export_approved",
                "expected_version": 1,
                "idempotency_key": "key-12345",
                "actor": "someone",
            }
        )
