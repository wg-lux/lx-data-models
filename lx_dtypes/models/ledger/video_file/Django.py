from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.utils.django_field_types import (
    BooleanFieldType,
    DateTimeField,
    OptionalCharFieldType,
    OptionalDateFieldType,
    OptionalFloatFieldType,
    OptionalIntegerFieldType,
    OptionalJSONFieldType,
)

from .DataDict import VideoFileDataDict


class VideoFileDjango(LedgerBaseModelDjango[VideoFileDataDict]):
    # Core identifiers and linkage fields
    if TYPE_CHECKING:
        center: models.CharField[str | None, str | None]  # type: ignore[misc]
        processor: models.CharField[str | None, str | None]  # type: ignore[misc]
        video_meta: models.CharField[str | None, str | None]  # type: ignore[misc]
        examination: models.CharField[str | None, str | None]  # type: ignore[misc]
        patient: models.CharField[str | None, str | None]  # type: ignore[misc]
        ai_model_meta: models.CharField[str | None, str | None]  # type: ignore[misc]
        state: models.CharField[str | None, str | None]  # type: ignore[misc]
        import_meta: models.CharField[str | None, str | None]  # type: ignore[misc]
        sensitive_meta: models.CharField[str | None, str | None]  # type: ignore[misc]

    center = models.CharField(max_length=255, blank=True, null=True)
    processor = models.CharField(max_length=255, blank=True, null=True)
    video_meta = models.CharField(max_length=255, blank=True, null=True)
    examination = models.CharField(max_length=255, blank=True, null=True)
    patient = models.CharField(max_length=255, blank=True, null=True)
    ai_model_meta = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    import_meta = models.CharField(max_length=255, blank=True, null=True)
    sensitive_meta = models.CharField(max_length=255, blank=True, null=True)

    # Content and storage metadata
    video_hash = models.CharField(max_length=255)
    processed_video_hash = models.CharField(max_length=255, blank=True, null=True)
    original_file_name = models.CharField(max_length=255, blank=True, null=True)
    storage_mode = models.CharField(max_length=64, blank=True, null=True)
    raw_streamable_relative_path = models.CharField(max_length=512, blank=True)
    processed_streamable_relative_path = models.CharField(max_length=512, blank=True)
    raw_file = models.FileField(max_length=500, blank=True, null=True)
    processed_file = models.FileField(max_length=500, blank=True, null=True)

    # Technical/processing fields
    uploaded_at = models.DateTimeField(blank=True, null=True)
    frame_dir = models.CharField(max_length=512, blank=True)
    fps = OptionalFloatFieldType()
    duration = OptionalFloatFieldType()
    frame_count = OptionalIntegerFieldType()
    width = OptionalIntegerFieldType()
    height = OptionalIntegerFieldType()
    suffix = OptionalCharFieldType(max_length=10)

    # JSON and export flags
    sequences = OptionalJSONFieldType(default=dict)
    export_segments_by_video: BooleanFieldType = models.BooleanField(default=False)

    # Timing
    date = OptionalDateFieldType(null=True, blank=True)
    meta = OptionalJSONFieldType(null=True)
    date_created = DateTimeField(auto_now_add=True)
    date_modified = DateTimeField(auto_now=True)

    @property
    def ddict_class(self) -> type[VideoFileDataDict]:
        return VideoFileDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
