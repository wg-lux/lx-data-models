from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonValue

type FfmpegProbeJsonValue = (
    JsonValue | None | list[FfmpegProbeJsonValue] | dict[str, FfmpegProbeJsonValue]
)
type FfmpegProbeJsonObject = dict[str, FfmpegProbeJsonValue]


class FfmpegProbeStreamPayload(BaseModel):
    """Validated subset of a single ffprobe stream entry."""

    model_config = ConfigDict(extra="forbid", strict=True)

    codec_type: str = Field(min_length=1)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    duration: str | None = None
    r_frame_rate: str | None = None
    avg_frame_rate: str | None = None
    codec_name: str | None = None
    pix_fmt: str | None = None
    color_range: str | None = None
    bit_rate: str | None = None
    nb_frames: str | None = None


class FfmpegMetaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    duration: float | None = Field(default=None, ge=0.0)
    frame_rate_num: int | None = Field(default=None, ge=0)
    frame_rate_den: int | None = Field(default=None, ge=0)
    codec_name: str | None = None
    pixel_format: str | None = None
    bit_rate: int | None = Field(default=None, ge=0)
    raw_probe_data: FfmpegProbeJsonObject | None = None


class FfmpegProbeFormatPayload(BaseModel):
    """Validated subset of the ffprobe format block."""

    model_config = ConfigDict(extra="forbid", strict=True)

    duration: str | None = None
    bit_rate: str | None = None


class FfmpegProbeDataPayload(BaseModel):
    """Validated ffprobe JSON payload used by video metadata extraction."""

    model_config = ConfigDict(extra="forbid", strict=True)

    streams: list[FfmpegProbeStreamPayload] = Field(default_factory=list)
    format: FfmpegProbeFormatPayload | None = None

    @property
    def video_streams(self) -> list[FfmpegProbeStreamPayload]:
        return [stream for stream in self.streams if stream.codec_type == "video"]


def ensure_sequence_of_probe_payloads(
    streams: Sequence[FfmpegProbeStreamPayload],
) -> list[FfmpegProbeStreamPayload]:
    return list(streams)


__all__ = [
    "FfmpegProbeDataPayload",
    "FfmpegProbeFormatPayload",
    "FfmpegProbeJsonObject",
    "FfmpegProbeJsonValue",
    "FfmpegProbeStreamPayload",
]
