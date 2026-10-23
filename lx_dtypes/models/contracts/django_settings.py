from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DjangoTemplateOptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    context_processors: tuple[str, ...] = Field(default_factory=tuple)


class DjangoTemplateConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    backend: str = Field(alias="BACKEND")
    dirs: tuple[str, ...] = Field(default_factory=tuple, alias="DIRS")
    app_dirs: bool = Field(alias="APP_DIRS")
    options: DjangoTemplateOptionsPayload = Field(alias="OPTIONS")


class DjangoCacheConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    backend: str = Field(alias="BACKEND")
    location: str = Field(alias="LOCATION")
    timeout: int = Field(alias="TIMEOUT")


class DjangoCacheSettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    default: DjangoCacheConfigPayload


class DjangoThrottleRatesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    user: str
    anon: str


class DjangoRestFrameworkSettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    default_throttle_classes: tuple[str, ...] = Field(alias="DEFAULT_THROTTLE_CLASSES")
    default_throttle_rates: DjangoThrottleRatesPayload = Field(
        alias="DEFAULT_THROTTLE_RATES"
    )


class DjangoBeatScheduleOptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    queue: str
    routing_key: str
    expires: int


class DjangoBeatScheduleEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    task: str
    schedule: int
    options: DjangoBeatScheduleOptionsPayload
