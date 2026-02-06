from pydantic import Field, model_validator

from lx_dtypes.models.base.app_base_model.ddict import StateBaseModelDataDict
from lx_dtypes.models.base.app_base_model.pydantic.StateBaseModel import StateBaseModel
from lx_dtypes.names import (
    PATIENT_VIDEO_SEGMENT_STATE_MODEL_LIST_TYPE_FIELDS,
    PATIENT_VIDEO_SEGMENT_STATE_MODEL_NESTED_FIELDS,
)


class PVideoSegmentStateDataDict(StateBaseModelDataDict):
    prediction: bool
    annotation: bool
    frames_extracted: bool
    is_validated: bool
    patient_video_segment: str


class PVideoSegmentState(StateBaseModel[PVideoSegmentStateDataDict]):
    prediction: bool = Field(default=False)
    annotation: bool = Field(default=False)
    frames_extracted: bool = Field(default=False)
    is_validated: bool = Field(default=False)
    patient_video_segment: str

    # model validator to make sure that either prediction or annotation is True
    @model_validator(mode="before")
    def check_prediction_or_annotation(cls, values):
        prediction = values.get("prediction", False)
        annotation = values.get("annotation", False)
        if not prediction and not annotation:
            raise ValueError("At least one of prediction or annotation must be True.")
        return values

    @property
    def ddict_class(self) -> type[PVideoSegmentStateDataDict]:
        return PVideoSegmentStateDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_STATE_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return PATIENT_VIDEO_SEGMENT_STATE_MODEL_NESTED_FIELDS
