"""Wire shapes of the media workflow API, snake_case on the wire.

Paths (below ``/api/media/``): ``videos|pdfs/<pk>/workflow/`` (item),
``videos|pdfs/<pk>/workflow/events/`` (POST, body
:class:`~.media_workflow.MediaWorkflowTransitionRequest`) and ``workflow/stages/``.
Clients reject any token outside these enums as a contract violation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .media_workflow import (
    AnnotationStage,
    EventOrigin,
    ExportApproval,
    MediaKind,
    PrivacyStage,
    ReleaseStage,
    TransitionRejection,
    WorkflowEvent,
    WorklistStage,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class StateSource(StrEnum):
    STORED = "stored"
    PROJECTED = "projected"


class AllowedEvent(_Frozen):
    event: WorkflowEvent
    origin: EventOrigin
    required_role: str | None = Field(default=None, min_length=1, max_length=128)
    blocked_reason: TransitionRejection | None = None

    @model_validator(mode="after")
    def users_are_offered_user_events_only(self) -> Self:
        if self.origin is not EventOrigin.USER:
            raise ValueError("Only user events may be offered to a client")
        return self


class BlockedStage(_Frozen):
    stage: ReleaseStage
    reason: TransitionRejection


class MediaWorkflowItem(_Frozen):
    kind: MediaKind
    record_id: int = Field(gt=0)
    version: int = Field(ge=0)
    source: StateSource
    privacy: PrivacyStage
    annotation: AnnotationStage
    release: ReleaseStage
    export_approval: ExportApproval
    allowed_events: tuple[AllowedEvent, ...] = ()
    blocked: tuple[BlockedStage, ...] = ()

    @model_validator(mode="after")
    def events_are_unique(self) -> Self:
        events = [allowed.event for allowed in self.allowed_events]
        if len(events) != len(set(events)):
            raise ValueError("An event may be offered only once")
        return self


class WorkflowInconsistency(_Frozen):
    """409 body: persisted facts contradict each other; never mapped to a state."""

    kind: MediaKind
    record_id: int = Field(gt=0)
    violations: tuple[str, ...] = Field(min_length=1)


class StageCount(_Frozen):
    stage: WorklistStage
    count: int = Field(ge=0)
    # Items still processed by the system; only decides whether to keep polling.
    transient: int = Field(ge=0)


class StageCounts(_Frozen):
    stages: tuple[StageCount, ...]

    @model_validator(mode="after")
    def one_row_per_stage(self) -> Self:
        stages = [row.stage for row in self.stages]
        if sorted(stages) != sorted(WorklistStage):
            raise ValueError("Every worklist stage needs exactly one row")
        return self
