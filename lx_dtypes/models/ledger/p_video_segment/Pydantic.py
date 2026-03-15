from pydantic import ValidationInfo, field_validator, model_validator

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.names import (
    PATIENT_VIDEO_SEGMENT_MODEL_LIST_TYPE_FIELDS,
    PATIENT_VIDEO_SEGMENT_MODEL_NESTED_FIELDS,
)

from .DataDict import PVideoSegmentDataDict, SerializedPVideoSegmentDataDict
from .state import PVideoSegmentState


class SerializedPVideoSegment(LedgerBaseModel[SerializedPVideoSegmentDataDict]):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool = False
    patient_video_segment_state: str

    @property
    def ddict_class(self) -> type[SerializedPVideoSegmentDataDict]:
        return SerializedPVideoSegmentDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_MODEL_NESTED_FIELDS


class PVideoSegment(LedgerBaseModel[PVideoSegmentDataDict]):
    start_frame_number: int
    end_frame_number: int
    patient_video_file: str
    label: str  # name of label in KB
    labelset: str  # name of labelset in KB
    export_segment: bool = False
    patient_video_segment_state: "PVideoSegmentState | None" = None

    @property
    def state(self) -> "PVideoSegmentState":
        state = self.patient_video_segment_state
        assert state is not None, (
            "patient_video_segment_state should never be None due to validator"
        )
        return state

    # ensure each segment always has a valid state referencing its UUID
    @model_validator(mode="after")
    def ensure_patient_video_segment_state(self) -> "PVideoSegment":
        state = self.patient_video_segment_state
        segment_uuid = str(self.uuid)

        if state is None:
            state = PVideoSegmentState(
                prediction=True,
                annotation=False,
                frames_extracted=False,
                is_validated=False,
                patient_video_segment=segment_uuid,
            )
        elif isinstance(state, PVideoSegmentState):
            if state.patient_video_segment != segment_uuid:
                state = state.model_copy(update={"patient_video_segment": segment_uuid})
        else:
            raise ValueError(
                "patient_video_segment_state must be a PVideoSegmentState instance or None"
            )

        self.patient_video_segment_state = state
        return self

    # validator to ensure that end_frame_number is greater than start_frame_number
    @field_validator("end_frame_number")
    def check_frame_numbers(cls, end_frame_number, info: ValidationInfo):
        start_frame_number = info.data.get("start_frame_number") if info.data else None
        if start_frame_number is not None and end_frame_number <= start_frame_number:
            raise ValueError("end_frame_number must be greater than start_frame_number")
        return end_frame_number

    @property
    def ddict_class(self) -> type[PVideoSegmentDataDict]:
        return PVideoSegmentDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPVideoSegmentDataDict]:
        return SerializedPVideoSegmentDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPVideoSegment"]:
        return SerializedPVideoSegment
