"""Portable time evidence reusing exact video segment timeline references."""

from fractions import Fraction
from typing import Literal, Self

from pydantic import ConfigDict, Field, model_validator

from lx_dtypes.models.model import FrozenContractModel

from .time import PtsTimestamp, TimeOffset
from .video_segment_timeline import VideoSegmentTimelineCoordinates

TimestampKind = Literal["pts", "electrosurgery", "examination"]


class TimeVideoReference(FrozenContractModel):
    timeline: Literal["generation", "recording"] = "generation"
    coordinates: VideoSegmentTimelineCoordinates

    def validate_timestamp(self, timestamp: PtsTimestamp) -> None:
        coordinates = (
            self.coordinates.generation
            if self.timeline == "generation"
            else self.coordinates.recording
        )
        if coordinates is None:
            raise ValueError("Recording clock references require verified coordinates")
        if Fraction(timestamp.time_base_num, timestamp.time_base_den) != Fraction(
            coordinates.time_base_num, coordinates.time_base_den
        ):
            raise ValueError("PTS time base disagrees with the referenced video")
        if timestamp.ticks not in (
            coordinates.first_presentation_timestamp,
            coordinates.last_presentation_timestamp,
        ):
            raise ValueError("PTS must identify an exact referenced segment endpoint")


class TimeOffsetEvidence(FrozenContractModel):
    """Clock anchors and video identities; every PTS clock has one reference."""

    model_config = ConfigDict(revalidate_instances="always")

    offset: TimeOffset
    video_references: dict[str, TimeVideoReference] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_video_references(self) -> Self:
        anchors = (self.offset.reference, self.offset.target)
        pts_clocks = {anchor.clock_id for anchor in anchors if anchor.kind == "pts"}
        if set(self.video_references) != pts_clocks:
            raise ValueError("Video references must match exactly the PTS clock IDs")
        if anchors[0].clock_id == anchors[1].clock_id and (
            anchors[0].kind != anchors[1].kind
            or (
                anchors[0].kind != "examination"
                and anchors[1].kind != "examination"
                and Fraction(anchors[0].time_base_num, anchors[0].time_base_den)
                != Fraction(anchors[1].time_base_num, anchors[1].time_base_den)
            )
        ):
            raise ValueError("One clock identity must have one kind and time base")
        for anchor in anchors:
            if isinstance(anchor, PtsTimestamp):
                self.video_references[anchor.clock_id].validate_timestamp(anchor)
        return self


class TimeOffsetExample(FrozenContractModel):
    example_id: str = Field(min_length=1, max_length=255, pattern=r"\S")
    role: Literal["reference", "training", "validation", "test"] = "reference"
    evidence: TimeOffsetEvidence


__all__ = [
    "TimeOffsetEvidence",
    "TimeOffsetExample",
    "TimeVideoReference",
    "TimestampKind",
]
