from __future__ import annotations

from pydantic import ConfigDict, Field

from lx_dtypes.models.contracts.text_anonymization import LLMMetadataPayload
from lx_dtypes.models.model import StrictContractModel


class LLMModelEntryPayload(StrictContractModel):
    name: str


class LLMModelCatalogEntryPayload(StrictContractModel):
    id: str


class LLMOllamaModelsPayload(StrictContractModel):
    models: list[LLMModelEntryPayload] = Field(default_factory=list)


class LLMVllmModelsPayload(StrictContractModel):
    data: list[LLMModelCatalogEntryPayload] = Field(default_factory=list)


class LLMMetadataCacheStatsPayload(StrictContractModel):
    hit_count: int
    miss_count: int
    hit_rate: float
    cache_size: int
    max_size: int


class LLMModelInfoPayload(StrictContractModel):
    current_model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    total_models: int = 0
    cache_stats: LLMMetadataCacheStatsPayload | None = None


class LLMFrameDataPayload(StrictContractModel):
    model_config = ConfigDict(extra="ignore")

    frame_index: int = 0
    timestamp: float = 0.0
    ocr_text: str = ""
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    has_text: bool = False
    has_patient_info: bool = False
    has_ui_elements: bool = False
    is_endoscopy_view: bool = False
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    frame_id: int | None = None
    frame_number: int | None = None

    def normalized_frame_index(self, fallback: int) -> int:
        if self.frame_number is not None:
            return self.frame_number
        if self.frame_id is not None:
            return self.frame_id
        return fallback


class LLMFrameContextPayload(StrictContractModel):
    total_frames: int = 0
    text_frames: int = 0
    quality_scores: list[float] = Field(default_factory=list)
    timestamps: list[float] = Field(default_factory=list)
    frame_types: dict[str, int] = Field(default_factory=dict)


class LLMTextTimelineEntryPayload(StrictContractModel):
    frame_index: int
    timestamp: float
    text_snippet: str
    confidence: float = Field(ge=0.0, le=1.0)


class LLMTemporalAnalysisPayload(StrictContractModel):
    model_config = ConfigDict(extra="ignore")

    duration_analysis: dict[str, float] = Field(default_factory=dict)
    text_appearance_timeline: list[LLMTextTimelineEntryPayload] = Field(
        default_factory=list
    )
    stability_scores: dict[str, float] = Field(default_factory=dict)
    change_points: list[int] = Field(default_factory=list)


class LLMEnrichedMetadataPayload(StrictContractModel):
    model_config = ConfigDict(extra="ignore")

    llm_extracted: LLMMetadataPayload = Field(default_factory=LLMMetadataPayload)
    frame_context: LLMFrameContextPayload = Field(
        default_factory=LLMFrameContextPayload
    )
    temporal_analysis: LLMTemporalAnalysisPayload = Field(
        default_factory=LLMTemporalAnalysisPayload
    )
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    source_frames: list[LLMFrameDataPayload] = Field(default_factory=list)


class LLMEvaluationResultPayload(StrictContractModel):
    model_config = ConfigDict(extra="ignore")

    data_sources_used: list[str] = Field(default_factory=list)
    confidence_comparison: dict[str, float] = Field(default_factory=dict)
    data_completeness: float = 0.0


__all__ = [
    "LLMEnrichedMetadataPayload",
    "LLMEvaluationResultPayload",
    "LLMFrameContextPayload",
    "LLMFrameDataPayload",
    "LLMMetadataCacheStatsPayload",
    "LLMModelCatalogEntryPayload",
    "LLMModelEntryPayload",
    "LLMModelInfoPayload",
    "LLMOllamaModelsPayload",
    "LLMTemporalAnalysisPayload",
    "LLMTextTimelineEntryPayload",
    "LLMVllmModelsPayload",
]
