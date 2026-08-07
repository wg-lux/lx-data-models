from collections.abc import Mapping
from datetime import datetime
from datetime import date as DateField

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.video_file import (
    VideoFileMetaJsonObject,
    VideoFilePayload,
)
from lx_dtypes.models.contracts.video_segments import VideoSegmentsPayloadDict

from .DataDict import VideoFileDataDict, SerializedVideoFileDataDict


class VideoFile(LedgerBaseModel[VideoFileDataDict]):
    center: str | None = None
    processor: str | None = None
    video_meta: str | None = None
    examination: str | None = None
    patient: str | None = None
    cases: list[str] | None = None
    ai_model_meta: str | None = None
    state: str | None = None
    import_meta: str | None = None
    sensitive_meta: str | None = None
    video_hash: str
    processed_video_hash: str | None = None
    original_file_name: str | None = None
    storage_mode: str = ""
    raw_streamable_relative_path: str = ""
    processed_streamable_relative_path: str = ""
    uploaded_at: datetime
    raw_file: str | None = None
    processed_file: str | None = None
    frame_dir: str = ""
    fps: float | None = None
    duration: float | None = None
    frame_count: int | None = None
    width: int | None = None
    height: int | None = None
    suffix: str | None = None
    sequences: VideoSegmentsPayloadDict = Field(default_factory=dict)
    export_segments_by_video: bool = False
    date: DateField | None = None
    meta: VideoFileMetaJsonObject | None = None
    date_created: datetime
    date_modified: datetime

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[VideoFileDataDict]:
        return VideoFileDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []

    @property
    def serialized_ddict_class(self) -> type[SerializedVideoFileDataDict]:
        return SerializedVideoFileDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedVideoFile"]:
        return SerializedVideoFile

    @classmethod
    def from_contract(
        cls, payload: VideoFilePayload | Mapping[str, object]
    ) -> "VideoFile":
        data = (
            payload.model_dump(mode="python")
            if isinstance(payload, VideoFilePayload)
            else dict(payload)
        )
        return cls.model_validate(
            {field: value for field, value in data.items() if field in cls.model_fields}
        )

    def to_contract(self) -> VideoFilePayload:
        return VideoFilePayload.model_validate(
            {
                field: value
                for field, value in self.model_dump().items()
                if field in VideoFilePayload.model_fields
            }
        )


class SerializedVideoFile(LedgerBaseModel[SerializedVideoFileDataDict]):
    center: str | None = None
    processor: str | None = None
    video_meta: str | None = None
    examination: str | None = None
    patient: str | None = None
    cases: list[str] | None = None
    ai_model_meta: str | None = None
    state: str | None = None
    import_meta: str | None = None
    sensitive_meta: str | None = None
    video_hash: str
    processed_video_hash: str | None = None
    original_file_name: str | None = None
    storage_mode: str = ""
    raw_streamable_relative_path: str = ""
    processed_streamable_relative_path: str = ""
    uploaded_at: datetime
    raw_file: str | None = None
    processed_file: str | None = None
    frame_dir: str = ""
    fps: float | None = None
    duration: float | None = None
    frame_count: int | None = None
    width: int | None = None
    height: int | None = None
    suffix: str | None = None
    sequences: VideoSegmentsPayloadDict = Field(default_factory=dict)
    export_segments_by_video: bool = False
    date: DateField | None = None
    meta: VideoFileMetaJsonObject | None = None
    date_created: datetime
    date_modified: datetime

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[SerializedVideoFileDataDict]:
        return SerializedVideoFileDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []

    @classmethod
    def from_contract(
        cls, payload: VideoFilePayload | Mapping[str, object]
    ) -> "SerializedVideoFile":
        data = (
            payload.model_dump(mode="python")
            if isinstance(payload, VideoFilePayload)
            else dict(payload)
        )
        return cls.model_validate(
            {field: value for field, value in data.items() if field in cls.model_fields}
        )

    def to_contract(self) -> VideoFilePayload:
        return VideoFilePayload.model_validate(
            {
                field: value
                for field, value in self.model_dump().items()
                if field in VideoFilePayload.model_fields
            }
        )
