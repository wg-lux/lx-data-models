from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.contracts.ai_dataset import AIModelType, DatasetType


type ApplicationSettingsDeploymentRole = Literal[
    "standalone",
    "site_node",
    "local_study_server",
    "central_hub",
]


class ApplicationSettingsBackupSourcePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    label: str = Field(min_length=1)
    path: str = Field(min_length=1)
    exists: bool
    file_count: int = Field(ge=0)

    @model_validator(mode="after")
    def _validate_file_count(self) -> "ApplicationSettingsBackupSourcePayload":
        if not self.exists and self.file_count != 0:
            raise ValueError("a missing backup source cannot contain files")
        return self


class ApplicationSettingsBackupStatusPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    ready: bool
    missing_paths: Sequence[str] = Field(default_factory=tuple)
    required_path_count: int = Field(ge=0)
    available_path_count: int = Field(ge=0)
    source_roots: Sequence[ApplicationSettingsBackupSourcePayload] = Field(
        default_factory=tuple
    )

    @model_validator(mode="after")
    def _validate_source_summary(self) -> "ApplicationSettingsBackupStatusPayload":
        if self.required_path_count != len(self.source_roots):
            raise ValueError("required_path_count must match source_roots")

        available_path_count = sum(source.exists for source in self.source_roots)
        if self.available_path_count != available_path_count:
            raise ValueError(
                "available_path_count must match the available source_roots"
            )

        missing_source_paths = {
            source.path for source in self.source_roots if not source.exists
        }
        if set(self.missing_paths) != missing_source_paths:
            raise ValueError("missing_paths must match the missing source_roots")

        if self.ready != (available_path_count == self.required_path_count):
            raise ValueError(
                "ready must reflect whether every source root is available"
            )
        return self


class ApplicationSettingsDataSetEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int | None = Field(default=None, ge=1)
    value: str = Field(min_length=1)
    label: str = Field(min_length=1)
    dataset_type: DatasetType
    ai_model_type: AIModelType
    is_active: bool
    name_count: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_model_type_matches_dataset_type(
        self,
    ) -> "ApplicationSettingsDataSetEntryPayload":
        allowed_by_dataset_type: dict[DatasetType, set[AIModelType]] = {
            "image": {"image_multilabel_classification", "phi_region_detector"},
            "video": {"video_segment_classification"},
        }
        if self.ai_model_type not in allowed_by_dataset_type[self.dataset_type]:
            raise ValueError("ai_model_type is not compatible with dataset_type")
        return self


class ApplicationSettingsDeploymentProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    deployment_role: ApplicationSettingsDeploymentRole
    hub_mode: bool
    enable_hub_transfers: bool
    transfer_api_enabled: bool
    transfer_require_secure_transport: bool
    transfer_require_mtls: bool

    @model_validator(mode="after")
    def _validate_derived_flags(
        self,
    ) -> "ApplicationSettingsDeploymentProfilePayload":
        expected_hub_mode = self.deployment_role == "central_hub"
        if self.hub_mode != expected_hub_mode:
            raise ValueError("hub_mode must match deployment_role")

        expected_transfer_api_enabled = expected_hub_mode and self.enable_hub_transfers
        if self.transfer_api_enabled != expected_transfer_api_enabled:
            raise ValueError(
                "transfer_api_enabled must match deployment_role and "
                "enable_hub_transfers"
            )
        return self


class ApplicationSettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int | None = None
    center_id: int | None = None
    center_name: str = ""
    processor_id: int | None = None
    processor_name: str = ""
    annotator_name: str = ""
    report_template_name: str = ""
    ai_dataset_id: int | None = None
    ai_dataset_name: str = ""
    ai_dataset_type: str = ""
    center_key: str | None = None
    updated_at: str | None = None
    deployment_profile: ApplicationSettingsDeploymentProfilePayload
    backup_status: ApplicationSettingsBackupStatusPayload


__all__ = [
    "ApplicationSettingsBackupSourcePayload",
    "ApplicationSettingsBackupStatusPayload",
    "ApplicationSettingsDataSetEntryPayload",
    "ApplicationSettingsDeploymentProfilePayload",
    "ApplicationSettingsDeploymentRole",
    "ApplicationSettingsPayload",
]
