"""Shared fields for the mutable and frozen frame-cache log contracts."""

from pydantic import BaseModel, Field


class FrameCacheManifestFields(BaseModel):
    frame_dir: str
    file_count: int
    missing_frame_numbers: list[int] = Field(default_factory=list)
    extra_frame_numbers: list[int] = Field(default_factory=list)
    invalid_file_names: list[str] = Field(default_factory=list)
    duplicate_frame_numbers: list[int] = Field(default_factory=list)
    unexpected_file_names: list[str] = Field(default_factory=list)
    expected_count: int | None = None


class FrameCacheValidationFields(BaseModel):
    db_extracted_frame_count: int
    db_missing_frame_numbers: list[int] = Field(default_factory=list)
    db_extra_frame_numbers: list[int] = Field(default_factory=list)
    db_path_mismatch_frame_numbers: list[int] = Field(default_factory=list)
    db_missing_file_frame_numbers: list[int] = Field(default_factory=list)
    valid: bool = False
