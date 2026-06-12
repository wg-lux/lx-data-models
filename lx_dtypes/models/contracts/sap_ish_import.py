from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime

from pydantic import ConfigDict, RootModel


type SapIshImportPayloadScalar = str | int | float | bool | None | datetime | date
type SapIshImportPayloadValue = (
    SapIshImportPayloadScalar
    | dict[str, "SapIshImportPayloadValue"]
    | list["SapIshImportPayloadValue"]
)
type SapIshImportPayload = dict[str, SapIshImportPayloadValue]


class SapIshDropFilePayload(RootModel[dict[str, SapIshImportPayloadValue]]):
    model_config = ConfigDict(frozen=True, strict=True)

    @property
    def as_dict(self) -> dict[str, SapIshImportPayloadValue]:
        return dict(self.root)


def dump_sap_ish_drop_file_payload(
    payload: SapIshDropFilePayload,
) -> SapIshImportPayload:
    return payload.as_dict


def validate_sap_ish_drop_file_payload(
    payload: Mapping[str, SapIshImportPayloadValue],
) -> SapIshDropFilePayload:
    return SapIshDropFilePayload.model_validate(dict(payload))


__all__ = [
    "SapIshDropFilePayload",
    "SapIshImportPayload",
    "SapIshImportPayloadScalar",
    "SapIshImportPayloadValue",
    "dump_sap_ish_drop_file_payload",
    "validate_sap_ish_drop_file_payload",
]
