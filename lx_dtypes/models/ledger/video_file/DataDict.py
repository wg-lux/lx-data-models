from datetime import datetime
from datetime import date as DateField
from typing import List

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.video_file import VideoFileMetaJsonObject
from lx_dtypes.models.contracts.video_segments import VideoSegmentsPayloadDict


class VideoFileDataDict(LedgerBaseModelDataDict):
    center: str | None
    processor: str | None
    video_meta: str | None
    examination: str | None
    patient: str | None
    cases: List[str] | None
    ai_model_meta: str | None
    state: str | None
    import_meta: str | None
    sensitive_meta: str | None
    video_hash: str
    processed_video_hash: str | None
    original_file_name: str | None
    storage_mode: str
    raw_streamable_relative_path: str
    processed_streamable_relative_path: str
    uploaded_at: datetime
    raw_file: str | None
    processed_file: str | None
    frame_dir: str
    fps: float | None
    duration: float | None
    frame_count: int | None
    width: int | None
    height: int | None
    suffix: str | None
    sequences: VideoSegmentsPayloadDict
    export_segments_by_video: bool
    date: DateField | None
    meta: VideoFileMetaJsonObject | None
    date_created: datetime
    date_modified: datetime


class SerializedVideoFileDataDict(VideoFileDataDict):
    center: str | None
    processor: str | None
    video_meta: str | None
    examination: str | None
    patient: str | None
    cases: List[str] | None
    ai_model_meta: str | None
    state: str | None
    import_meta: str | None
    sensitive_meta: str | None
