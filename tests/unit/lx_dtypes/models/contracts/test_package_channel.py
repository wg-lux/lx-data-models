"""Package kinds, lx-package/1 manifests and lx-package-channel/1 indexes."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    PACKAGE_KIND_ALLOWED_DEPENDENCIES,
    LxPackageManifest,
    PackageChannelEntry,
    PackageChannelIndex,
    PackageKind,
    package_kind_dependency_allowed,
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig

DIGEST = "a" * 64


def _entry(**changes: object) -> dict[str, object]:
    return {
        "name": "dgvs_reporting",
        "version": "0.2.0",
        "package_kind": "report_templates",
        "sha256": DIGEST,
        "size": 123456,
        "path": f"packages/{DIGEST}.zip",
        "published_at": "2026-11-20T10:00:00Z",
        **changes,
    }


def test_package_kinds_are_exactly_the_contract_set() -> None:
    assert {kind.value for kind in PackageKind} == {
        "terminology",
        "report_templates",
        "study",
        "application_data",
    }
    assert set(PACKAGE_KIND_ALLOWED_DEPENDENCIES) == set(PackageKind)


@pytest.mark.parametrize(
    "kind,dependency,allowed",
    [
        ("terminology", "terminology", True),
        ("terminology", "report_templates", False),
        ("terminology", "application_data", True),
        ("report_templates", "terminology", True),
        ("report_templates", "report_templates", True),
        ("report_templates", "application_data", True),
        ("report_templates", "study", False),
        ("study", "terminology", True),
        ("study", "report_templates", True),
        ("study", "application_data", True),
        ("study", "study", False),
        ("application_data", "application_data", True),
        ("application_data", "terminology", True),
        ("application_data", "report_templates", False),
        ("application_data", "study", False),
    ],
)
def test_dependency_rules(kind: str, dependency: str, allowed: bool) -> None:
    assert (
        package_kind_dependency_allowed(PackageKind(kind), PackageKind(dependency))
        is allowed
    )


def test_config_kind_is_optional_and_never_defaulted(tmp_path: Path) -> None:
    config = KnowledgeBaseConfig.model_validate({"name": "terms", "version": "1"})
    assert config.package_kind is None
    declared = KnowledgeBaseConfig.model_validate(
        {"name": "terms", "version": "1", "package_kind": "terminology"}
    )
    assert declared.package_kind is PackageKind.terminology
    with pytest.raises(ValidationError):
        KnowledgeBaseConfig.model_validate(
            {"name": "terms", "version": "1", "package_kind": "concepts"}
        )
    manifest = tmp_path / "config.yaml"
    manifest.write_text(
        "name: terms\nversion: '1'\npackage_kind: application_data\n",
        encoding="utf-8",
    )
    assert (
        KnowledgeBaseConfig.from_yaml_file(manifest).package_kind
        is PackageKind.application_data
    )


def test_manifest_roundtrip_is_deterministic() -> None:
    raw = {
        "schema": "lx-package/1",
        "name": "dgvs_reporting",
        "version": "0.2.0",
        "package_kind": "report_templates",
    }
    manifest = LxPackageManifest.model_validate_json(json.dumps(raw))
    assert manifest.package_kind is PackageKind.report_templates
    assert json.loads(manifest.to_json_bytes()) == raw
    assert manifest.to_json_bytes() == (
        LxPackageManifest.model_validate(raw).to_json_bytes()
    )


@pytest.mark.parametrize(
    "change",
    [
        {"schema": "lx-package/2"},
        {"package_kind": "concepts"},
        {"package_kind": None},
        {"name": ""},
        {"name": "../escape"},
        {"version": "1.0@x"},
        {"unexpected": True},
    ],
)
def test_manifest_rejects_invalid_documents(change: dict[str, object]) -> None:
    raw: dict[str, object] = {
        "schema": "lx-package/1",
        "name": "terms",
        "version": "1.0.0",
        "package_kind": "terminology",
        **change,
    }
    with pytest.raises(ValidationError):
        LxPackageManifest.model_validate_json(json.dumps(raw))


def test_channel_index_accepts_contract_example() -> None:
    index = PackageChannelIndex.model_validate_json(
        json.dumps(
            {
                "schema": "lx-package-channel/1",
                "channel": "gs-02",
                "generated_at": "2026-11-20T10:00:00Z",
                "packages": [_entry()],
            }
        )
    )
    entry = index.entry("dgvs_reporting", "0.2.0")
    assert entry.package_kind is PackageKind.report_templates
    assert entry.matches_manifest(
        LxPackageManifest.model_validate(
            {
                "schema": "lx-package/1",
                "name": "dgvs_reporting",
                "version": "0.2.0",
                "package_kind": "report_templates",
            }
        )
    )
    with pytest.raises(LookupError):
        index.entry("dgvs_reporting", "0.1.0")


@pytest.mark.parametrize(
    "change",
    [
        {"sha256": "A" * 64, "path": f"packages/{'A' * 64}.zip"},
        {"sha256": "a" * 63, "path": f"packages/{'a' * 63}.zip"},
        {"path": f"packages/{'b' * 64}.zip"},
        {"path": f"{DIGEST}.zip"},
        {"size": 0},
        {"size": "12"},
        {"published_at": "2026-11-20T10:00:00"},
        {"published_at": "2026-11-20T11:00:00+01:00"},
        {"package_kind": "terminologie"},
        {"extra": 1},
    ],
)
def test_channel_entry_rejects_invalid_values(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        PackageChannelEntry.model_validate_json(json.dumps(_entry(**change)))


@pytest.mark.parametrize(
    "packages",
    [
        [_entry(), _entry()],
        [_entry(), _entry(version="0.3.0")],
    ],
)
def test_channel_index_rejects_duplicate_identities_or_bytes(
    packages: list[dict[str, object]],
) -> None:
    with pytest.raises(ValidationError):
        PackageChannelIndex.model_validate_json(
            json.dumps(
                {
                    "schema": "lx-package-channel/1",
                    "channel": "gs-02",
                    "generated_at": "2026-11-20T10:00:00Z",
                    "packages": packages,
                }
            )
        )


def test_channel_index_rejects_unknown_schema_and_fields() -> None:
    base = {
        "schema": "lx-package-channel/1",
        "channel": "gs-02",
        "generated_at": "2026-11-20T10:00:00Z",
        "packages": [],
    }
    PackageChannelIndex.model_validate_json(json.dumps(base))
    for change in ({"schema": "lx-package-channel/2"}, {"signature": "x"}):
        with pytest.raises(ValidationError):
            PackageChannelIndex.model_validate_json(json.dumps({**base, **change}))
