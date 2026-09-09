from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _empty_int_list() -> list[int]:
    return []


def _empty_float_list() -> list[float]:
    return []


def _empty_str_list() -> list[str]:
    return []


class TesseractOCRData(BaseModel):
    """Normalized columnar OCR payload returned by pytesseract."""

    model_config = ConfigDict(extra="forbid")

    left: list[int] = Field(default_factory=_empty_int_list)
    top: list[int] = Field(default_factory=_empty_int_list)
    width: list[int] = Field(default_factory=_empty_int_list)
    height: list[int] = Field(default_factory=_empty_int_list)
    conf: list[float] = Field(default_factory=_empty_float_list)
    text: list[str] = Field(default_factory=_empty_str_list)

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> TesseractOCRData:
        lengths = {
            len(self.left),
            len(self.top),
            len(self.width),
            len(self.height),
            len(self.conf),
            len(self.text),
        }
        if len(lengths) != 1:
            raise ValueError("tesseract OCR columns must have the same length")
        return self


class TesseractWordConfidence(BaseModel):
    """A validated word-level OCR detection and its confidence payload."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    start_x: int = Field(alias="startX")
    start_y: int = Field(alias="startY")
    end_x: int = Field(alias="endX")
    end_y: int = Field(alias="endY")
    confidence: float
    text: str

    @model_validator(mode="after")
    def validate_box(self) -> TesseractWordConfidence:
        if self.end_x <= self.start_x:
            raise ValueError("end_x must be greater than start_x")
        if self.end_y <= self.start_y:
            raise ValueError("end_y must be greater than start_y")
        if self.text.strip() == "":
            raise ValueError("text must not be empty")
        return self


class PixelBoundingBoxCore(BaseModel):
    """Strict pixel-space bounding box with absolute coordinates."""

    model_config = ConfigDict(extra="forbid", strict=True)

    x1: int
    y1: int
    x2: int
    y2: int

    @model_validator(mode="after")
    def validate_bounds(self) -> PixelBoundingBoxCore:
        if self.x1 < 0 or self.y1 < 0:
            raise ValueError("x1 and y1 must be >= 0")
        if self.x2 <= self.x1:
            raise ValueError("x2 must be greater than x1")
        if self.y2 <= self.y1:
            raise ValueError("y2 must be greater than y1")
        return self

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)


class OcrTextBoxCore(BaseModel):
    """Normalized OCR word payload with an absolute pixel box."""

    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    box: PixelBoundingBoxCore

    @model_validator(mode="after")
    def validate_text(self) -> OcrTextBoxCore:
        if self.text.strip() == "":
            raise ValueError("text must not be empty")
        return self

    def to_ocr_result(self) -> tuple[str, tuple[int, int, int, int]]:
        return (self.text, self.box.as_tuple())


class EastDetectionConfidenceCore(BaseModel):
    """Confidence payload for EAST detections."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, strict=True)

    start_x: int = Field(alias="startX")
    start_y: int = Field(alias="startY")
    end_x: int = Field(alias="endX")
    end_y: int = Field(alias="endY")
    confidence: float

    @model_validator(mode="after")
    def validate_box(self) -> EastDetectionConfidenceCore:
        if self.end_x <= self.start_x:
            raise ValueError("end_x must be greater than start_x")
        if self.end_y <= self.start_y:
            raise ValueError("end_y must be greater than start_y")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        return self


__all__ = [
    "EastDetectionConfidenceCore",
    "OcrTextBoxCore",
    "PixelBoundingBoxCore",
    "TesseractOCRData",
    "TesseractWordConfidence",
]
