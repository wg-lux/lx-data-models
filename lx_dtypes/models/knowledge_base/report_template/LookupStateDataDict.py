from __future__ import annotations

from typing import Any, List, TypedDict


class RequirementSetSummaryDataDict(TypedDict):
    id: int
    name: str
    type: str


class LookupInitRequestDataDict(TypedDict, total=False):
    patient_examination_id: int
    user_tags: List[str]


class LookupPartsPatchRequestDataDict(TypedDict):
    updates: dict[str, Any]


class LookupStateDataDict(TypedDict, total=False):
    patient_examination_id: int
    requirement_sets: List[RequirementSetSummaryDataDict]
    available_findings: List[int]
    required_findings: List[int]
    requirement_defaults: dict[str, Any]
    classification_choices: dict[str, Any]
    requirements_by_set: dict[str, List[dict[str, Any]]]
    requirement_status: dict[str, bool]
    requirement_set_status: dict[str, bool]
    suggested_actions: dict[str, List[dict[str, Any]]]
    candidate_requirement_set_ids: List[int]
    candidate_requirement_set_confidence: float
    selected_requirement_set_ids: List[int]
    selected_choices: dict[str, Any]


class LookupDerivedUpdatesDataDict(TypedDict, total=False):
    requirements_by_set: dict[str, List[dict[str, Any]]]
    requirement_status: dict[str, bool]
    requirement_set_status: dict[str, bool]
    requirement_defaults: dict[str, Any]
    classification_choices: dict[str, Any]
    suggested_actions: dict[str, List[dict[str, Any]]]
    candidate_requirement_set_ids: List[int]
    candidate_requirement_set_confidence: float


class LookupRecomputeResponseDataDict(TypedDict):
    ok: bool
    token: str
    updates: LookupDerivedUpdatesDataDict
