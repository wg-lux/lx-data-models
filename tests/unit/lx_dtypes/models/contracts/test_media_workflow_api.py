import json

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.media_workflow_api import (
    MediaWorkflowItem,
    StageCounts,
)

ITEM = {
    "kind": "video",
    "record_id": 42,
    "version": 7,
    "source": "stored",
    "privacy": "awaiting_validation",
    "annotation": "in_progress",
    "release": "not_released",
    "export_approval": "none",
    "allowed_events": [
        {
            "event": "anonymization_validated",
            "origin": "user",
            "required_role": "validator",
            "blocked_reason": None,
        }
    ],
    "blocked": [{"stage": "export_ready", "reason": "privacy_track_incomplete"}],
}


def _item(**patch: object) -> MediaWorkflowItem:
    return MediaWorkflowItem.model_validate_json(json.dumps({**ITEM, **patch}))


def test_item_response_round_trips() -> None:
    item = _item()
    assert MediaWorkflowItem.model_validate_json(item.model_dump_json()) == item
    assert item.allowed_events[0].blocked_reason is None


@pytest.mark.parametrize(
    "patch",
    [
        {"privacy": "unknown_stage"},
        {"kind": "image"},
        {"record_id": 0},
        {"extra_key": 1},
        {"allowed_events": [{"event": "raw_purged", "origin": "system"}]},
        {
            "allowed_events": [
                {"event": "export_approved", "origin": "user"},
                {"event": "export_approved", "origin": "user"},
            ]
        },
    ],
)
def test_item_rejects_contract_violations(patch: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _item(**patch)


def test_stage_counts_require_each_stage_once() -> None:
    rows = [
        {"stage": "validate", "count": 3, "transient": 1},
        {"stage": "annotate", "count": 5, "transient": 0},
        {"stage": "approve_export", "count": 0, "transient": 0},
    ]
    assert (
        len(StageCounts.model_validate_json(json.dumps({"stages": rows})).stages) == 3
    )
    with pytest.raises(ValidationError):
        StageCounts.model_validate_json(json.dumps({"stages": rows[:2]}))
    with pytest.raises(ValidationError):
        StageCounts.model_validate_json(json.dumps({"stages": [*rows, rows[0]]}))
