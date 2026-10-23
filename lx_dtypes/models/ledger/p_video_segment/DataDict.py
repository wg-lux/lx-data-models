from typing import NotRequired

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.video_segment_timeline import (
    VideoSegmentTimelineCoordinatesData,
)


class SerializedPVideoSegmentDataDict(LedgerBaseModelDataDict):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool
    timeline_coordinates: NotRequired[VideoSegmentTimelineCoordinatesData | None]
    # annotation_meta: AnnotationMetaDataDict


class PVideoSegmentDataDict(LedgerBaseModelDataDict):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool
    timeline_coordinates: NotRequired[VideoSegmentTimelineCoordinatesData | None]
    # annotation_meta: AnnotationMetaDataDict
