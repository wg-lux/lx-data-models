from __future__ import annotations

from pydantic import ConfigDict, RootModel, field_validator

from .json_types import JsonValue


class CodemodRenameMapPayload(RootModel[dict[str, str]]):
    model_config = ConfigDict(frozen=True, strict=True)

    @field_validator("root", mode="after")
    @classmethod
    def validate_rename_map(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("rename map must not be empty")

        normalized: dict[str, str] = {}
        for legacy_name, target_name in value.items():
            legacy_field = legacy_name.strip()
            target_field = target_name.strip()
            if not legacy_field or not target_field:
                raise ValueError("rename map keys and values must not be blank")
            normalized[legacy_field] = target_field
        return normalized

    @property
    def renames(self) -> dict[str, str]:
        return dict(self.root)


def validate_codemod_rename_map(payload: JsonValue) -> CodemodRenameMapPayload:
    return CodemodRenameMapPayload.model_validate(payload)


__all__ = [
    "CodemodRenameMapPayload",
    "validate_codemod_rename_map",
]
