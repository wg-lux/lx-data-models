from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MultiLabelBackboneName(str, Enum):
    EFFICIENT_NET_B4 = "EfficientNetB4"
    REGNET_X_800MF = "RegNetX800MF"


class MultiLabelClassificationConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    labels: list[str] = Field(min_length=1)
    lr: float = Field(gt=0)
    weight_decay: float = Field(ge=0)
    pos_weight: float = Field(gt=0)
    model_type: MultiLabelBackboneName = MultiLabelBackboneName.EFFICIENT_NET_B4
    load_imagenet_weights: bool = False


__all__ = [
    "MultiLabelBackboneName",
    "MultiLabelClassificationConfigPayload",
]
