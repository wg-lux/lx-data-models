from typing import Dict

from pydantic import Field, model_validator

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.base.file.patient_file_mixin import (
    PatientFileMixIn,
    SerializedPatientFileMixIn,
)
from lx_dtypes.models.ledger.p_video.DataDict import (
    PatientVideoFileDataDict,
    # RawPatientVideoFileDataDict,
    SerializedPatientVideoFileDataDict,
    # SerializedRawPatientVideoFileDataDict,
)
from lx_dtypes.models.ledger.p_video_segment.Pydantic import PVideoSegment
from lx_dtypes.models.meta.SensitiveMeta import SensitiveMeta
from lx_dtypes.names import (
    PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS,
    PATIENT_VIDEO_FILE_MODEL_NESTED_FIELDS,
    # RAW_PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS,
    # RAW_PATIENT_VIDEO_FILE_MODEL_NESTED_FIELDS,
)

from .state import AnonymizationState


class PatientVideoFile(PatientFileMixIn, LedgerBaseModel[PatientVideoFileDataDict]):
    patient_video_segments: Dict[str, "PVideoSegment"] = Field(default_factory=dict)
    anonymization_state: AnonymizationState = Field(
        default=AnonymizationState.NOT_STARTED
    )
    sensitive_meta: "SensitiveMeta | None" = None

    @model_validator(mode="after")
    def ensure_sensitive_meta(self) -> "PatientVideoFile":
        if self.sensitive_meta is None:
            self.sensitive_meta = SensitiveMeta()
        return self

    def create_segment(
        self, start_frame_number: int, end_frame_number: int, label: str, labelset: str
    ) -> "PVideoSegment":
        segment = PVideoSegment.model_validate(
            {
                "start_frame_number": start_frame_number,
                "end_frame_number": end_frame_number,
                "patient_video_file": str(self.uuid),
                "label": label,
                "labelset": labelset,
            }
        )
        self.patient_video_segments[str(segment.uuid)] = segment
        return segment

    def update_segment(self, segment_uuid: str, **kwargs) -> "PVideoSegment":
        if segment_uuid not in self.patient_video_segments:
            raise ValueError(
                f"Segment with UUID {segment_uuid} not found in patient video file."
            )
        segment = self.patient_video_segments[segment_uuid]
        updated_data = segment.model_dump()
        updated_data.update(kwargs)
        updated_segment = PVideoSegment.model_validate(updated_data)
        self.patient_video_segments[segment_uuid] = updated_segment
        return updated_segment

    @property
    def ddict_class(self) -> type[PatientVideoFileDataDict]:
        return PatientVideoFileDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return PATIENT_VIDEO_FILE_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedPatientVideoFileDataDict]:
        return SerializedPatientVideoFileDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPatientVideoFile"]:
        return SerializedPatientVideoFile

    @property
    def serialized_model(self) -> "SerializedPatientVideoFile":
        """
        Produce a serialized model with nested ledger models replaced by UUID strings.

        Returns:
            An instance of the serialized model class (`serialized_model_class`) containing the model's data with nested ledger items flattened to UUID strings.
        """
        data = self.model_dump()

        file = self.file
        data["file"] = str(file)
        data.pop("fnd", None)

        for field in self.nested_fields():
            data[field] = self._flatten_nested(data.get(field))

        serialized_model = self.serialized_model_class().model_validate(data)
        return serialized_model


class SerializedPatientVideoFile(
    SerializedPatientFileMixIn, LedgerBaseModel[SerializedPatientVideoFileDataDict]
):
    @property
    def ddict_class(self) -> type[SerializedPatientVideoFileDataDict]:
        return SerializedPatientVideoFileDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []


# class RawPatientVideoFile(
#     PatientFileMixIn, LedgerBaseModel[RawPatientVideoFileDataDict]
# ):
#     @property
#     def serialized_ddict_class(self) -> type[SerializedRawPatientVideoFileDataDict]:
#         return SerializedRawPatientVideoFileDataDict

#     @classmethod
#     def serialized_model_class(cls) -> type["SerializedPatientRawVideoFile"]:
#         return SerializedPatientRawVideoFile

#     @property
#     def ddict_class(self) -> type[RawPatientVideoFileDataDict]:
#         return RawPatientVideoFileDataDict

#     @classmethod
#     def list_type_fields(cls) -> list[str]:
#         return RAW_PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS

#     @classmethod
#     def nested_fields(cls) -> list[str]:
#         return RAW_PATIENT_VIDEO_FILE_MODEL_NESTED_FIELDS

#     @property
#     def serialized_model(self) -> "SerializedPatientRawVideoFile":
#         """
#         Produce a serialized model with nested ledger models replaced by UUID strings.

#         Returns:
#             An instance of the serialized model class (`serialized_model_class`) containing the model's data with nested ledger items flattened to UUID strings.
#         """
#         data = self.model_dump()

#         file = self.file
#         data["file"] = str(file)
#         data.pop("fnd", None)

#         for field in self.nested_fields():
#             data[field] = self._flatten_nested(data.get(field))

#         serialized_model = self.serialized_model_class().model_validate(data)
#         return serialized_model


# class SerializedPatientRawVideoFile(
#     SerializedPatientFileMixIn, LedgerBaseModel[SerializedRawPatientVideoFileDataDict]
# ):
#     @property
#     def ddict_class(self) -> type[SerializedRawPatientVideoFileDataDict]:
#         return SerializedRawPatientVideoFileDataDict

#     @classmethod
#     def list_type_fields(cls) -> list[str]:
#         return RAW_PATIENT_VIDEO_FILE_MODEL_LIST_TYPE_FIELDS

#     @classmethod
#     def nested_fields(cls) -> list[str]:
#         return []


# ########## Django
