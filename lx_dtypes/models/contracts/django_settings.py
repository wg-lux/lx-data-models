from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class DjangoTemplateOptionsPayload(FrozenContractModel):
    context_processors: tuple[str, ...] = Field(default_factory=tuple)


class DjangoTemplateConfigPayload(FrozenContractModel):
    backend: str = Field(alias="BACKEND")
    dirs: tuple[str, ...] = Field(default_factory=tuple, alias="DIRS")
    app_dirs: bool = Field(alias="APP_DIRS")
    options: DjangoTemplateOptionsPayload = Field(alias="OPTIONS")


class DjangoCacheConfigPayload(FrozenContractModel):
    backend: str = Field(alias="BACKEND")
    location: str = Field(alias="LOCATION")
    timeout: int = Field(alias="TIMEOUT")


class DjangoCacheSettingsPayload(FrozenContractModel):
    default: DjangoCacheConfigPayload


class DjangoThrottleRatesPayload(FrozenContractModel):
    user: str
    anon: str


class DjangoRestFrameworkSettingsPayload(FrozenContractModel):
    default_throttle_classes: tuple[str, ...] = Field(alias="DEFAULT_THROTTLE_CLASSES")
    default_throttle_rates: DjangoThrottleRatesPayload = Field(
        alias="DEFAULT_THROTTLE_RATES"
    )


class DjangoBeatScheduleOptionsPayload(FrozenContractModel):
    queue: str
    routing_key: str
    expires: int


class DjangoBeatScheduleEntryPayload(FrozenContractModel):
    task: str
    schedule: int
    options: DjangoBeatScheduleOptionsPayload
