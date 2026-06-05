from __future__ import annotations

from datetime import datetime
from typing import Literal, NotRequired, Self, TypeAlias, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator


MediaStreamDisposition: TypeAlias = Literal["attachment", "inline"]
MediaStreamFileKind: TypeAlias = Literal["processed", "raw"]
StreamThrottleMode: TypeAlias = Literal["normal", "streaming"]


class ByteRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        return self

    @property
    def length(self) -> int:
        return self.end - self.start + 1


class MediaOperationLeaseSummaryPayload(TypedDict):
    lease_type: str
    expires_at: datetime


class MediaOperationLeaseSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        strict=True,
    )

    lease_type: str
    expires_at: datetime


class FfmpegStreamThrottleStatePayload(TypedDict):
    mode: StreamThrottleMode
    active_stream_leases: int
    expired_leases: int
    checked_at: str
    next_stream_lease_expiry: NotRequired[str]


class FfmpegStreamThrottleState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    mode: StreamThrottleMode
    active_stream_leases: NonNegativeInt
    expired_leases: NonNegativeInt
    checked_at: datetime


class FfmpegActiveStreamThrottleState(FfmpegStreamThrottleState):
    next_stream_lease_expiry: datetime


def dump_media_operation_lease_summary(
    payload: MediaOperationLeaseSummary,
) -> MediaOperationLeaseSummaryPayload:
    return cast(MediaOperationLeaseSummaryPayload, payload.model_dump(mode="python"))


def dump_ffmpeg_stream_throttle_state(
    payload: FfmpegStreamThrottleState,
) -> FfmpegStreamThrottleStatePayload:
    return cast(FfmpegStreamThrottleStatePayload, payload.model_dump(mode="json"))


__all__ = [
    "ByteRange",
    "FfmpegActiveStreamThrottleState",
    "FfmpegStreamThrottleState",
    "FfmpegStreamThrottleStatePayload",
    "MediaOperationLeaseSummary",
    "MediaOperationLeaseSummaryPayload",
    "MediaStreamDisposition",
    "MediaStreamFileKind",
    "StreamThrottleMode",
    "dump_ffmpeg_stream_throttle_state",
    "dump_media_operation_lease_summary",
]
