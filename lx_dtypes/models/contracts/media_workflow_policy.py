"""Decisions around the media workflow that carry payloads rather than states.

Covers the validation acknowledgement, the examination key that links report and
video annotations, the shared-salt precondition for hub patient matching and the
per-location outcome of a consent withdrawal. Only anonymous hashes appear here;
no patient identifiers and no salt values.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class AnonymizationValidationAcknowledgement(_Frozen):
    """Validation is final: the validator confirms once that nothing identifying remains visible."""

    confirmed_no_identifying_content_visible: Literal[True]
    hide_prompt_in_future: bool = False


class ExaminationLinkKey(_Frozen):
    """Maps a report and a video of the same examination without exposing the patient."""

    sensitive_meta_hash: Sha256Hex
    examination_date: date


class ExaminationAnnotationLink(_Frozen):
    key: ExaminationLinkKey
    video_id: int = Field(gt=0)
    report_id: int = Field(gt=0)


class SharedSaltMatchingPrecondition(_Frozen):
    """Hub-side patient matching is only meaningful when both nodes use one salt generation."""

    local_salt_fingerprint: str = Field(min_length=8, max_length=128)
    hub_salt_fingerprint: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def same_salt_generation(self) -> Self:
        if self.local_salt_fingerprint != self.hub_salt_fingerprint:
            raise ValueError("Hub matching requires the same identity salt generation")
        return self


class WithdrawalLocation(StrEnum):
    LOCAL = "local"
    HUB = "hub"
    FROZEN_DATASETS = "frozen_datasets"


class DeletionStatus(StrEnum):
    DELETED = "deleted"
    NOT_PRESENT = "not_present"
    PENDING = "pending"
    NOT_POSSIBLE = "not_possible"


class LocationDeletionOutcome(_Frozen):
    location: WithdrawalLocation
    status: DeletionStatus
    reason: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def impossible_deletion_needs_reason(self) -> Self:
        if self.status is DeletionStatus.NOT_POSSIBLE and not self.reason.strip():
            raise ValueError("A deletion that is not possible must state why")
        return self


class ConsentWithdrawalOutcome(_Frozen):
    """Delete everywhere possible; whatever remains is explicit, never silently skipped."""

    outcomes: tuple[LocationDeletionOutcome, ...]

    @model_validator(mode="after")
    def cover_every_location_once(self) -> Self:
        locations = [outcome.location for outcome in self.outcomes]
        if sorted(locations) != sorted(WithdrawalLocation):
            raise ValueError("Every withdrawal location needs exactly one outcome")
        return self

    @property
    def local_erased(self) -> bool:
        return any(
            outcome.location is WithdrawalLocation.LOCAL
            and outcome.status in {DeletionStatus.DELETED, DeletionStatus.NOT_PRESENT}
            for outcome in self.outcomes
        )
