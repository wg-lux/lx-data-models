from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field


class ModelMetaCreateFromFileKwargsData(TypedDict, total=False):
    activation: str
    mean: str
    std: str
    size_x: int
    size_y: int
    axes: str
    batchsize: int
    num_workers: int
    description: str


class ModelMetaCreateFromFileKwargsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    activation: str = Field(default="sigmoid", min_length=1)
    mean: str = Field(default="0.45211223,0.27139644,0.19264949", min_length=1)
    std: str = Field(default="0.31418097,0.21088019,0.16059452", min_length=1)
    size_x: int = Field(default=716, ge=1)
    size_y: int = Field(default=716, ge=1)
    axes: str = Field(default="2,0,1", min_length=1)
    batchsize: int = Field(default=16, ge=1)
    num_workers: int = Field(default=0, ge=0)
    description: str = ""


class ModelMetaCreateFromFilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    activation: str = Field(default="sigmoid", min_length=1)
    mean: str = Field(default="0.45211223,0.27139644,0.19264949", min_length=1)
    std: str = Field(default="0.31418097,0.21088019,0.16059452", min_length=1)
    size_x: int = Field(default=716, ge=1)
    size_y: int = Field(default=716, ge=1)
    axes: str = Field(default="2,0,1", min_length=1)
    batchsize: int = Field(default=16, ge=1)
    num_workers: int = Field(default=0, ge=0)
    description: str = ""


class ModelMetaInferredDefaultsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str = Field(min_length=1)
    activation: str = Field(min_length=1)
    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    size_x: int = Field(ge=1)
    size_y: int = Field(ge=1)
    description: str = ""


__all__ = [
    "ModelMetaCreateFromFileKwargsData",
    "ModelMetaCreateFromFileKwargsPayload",
    "ModelMetaCreateFromFilePayload",
    "ModelMetaInferredDefaultsPayload",
]
