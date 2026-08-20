from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import validate_codemod_rename_map
from lx_dtypes.models.contracts.json_types import JsonValue


def test_validate_codemod_rename_map_returns_strict_mapping() -> None:
    payload: dict[str, JsonValue] = {
        "date_created": "created_at",
        "date_modified": "updated_at",
    }

    rename_map = validate_codemod_rename_map(payload)

    assert rename_map.renames == {
        "date_created": "created_at",
        "date_modified": "updated_at",
    }


def test_validate_codemod_rename_map_strips_names() -> None:
    payload: dict[str, JsonValue] = {" date_created ": " created_at "}

    rename_map = validate_codemod_rename_map(payload)

    assert rename_map.renames == {"date_created": "created_at"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"date_created": ""},
        {"": "created_at"},
        {"date_created": 7},
    ],
)
def test_validate_codemod_rename_map_rejects_invalid_payloads(
    payload: dict[str, JsonValue],
) -> None:
    with pytest.raises(ValidationError):
        validate_codemod_rename_map(payload)
