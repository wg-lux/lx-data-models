from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class SerializedPVideoSegmentDataDict(LedgerBaseModelDataDict):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool
    # annotation_meta: AnnotationMetaDataDict


class PVideoSegmentDataDict(LedgerBaseModelDataDict):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool
    # annotation_meta: AnnotationMetaDataDict
