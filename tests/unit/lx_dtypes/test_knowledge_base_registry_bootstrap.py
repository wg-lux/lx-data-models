from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from lx_dtypes.knowledge_base_registry import PACKAGED_KNOWLEDGE_BASE_MODULES
from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    get_packaged_knowledge_base,
)
from lx_dtypes.scripts.kb_registry import main


def _write_custom_bundle(
    root: Path,
    *,
    module_name: str = "custom_reporting",
    version: str = "7.4.0",
) -> None:
    module_dir = root / module_name
    data_dir = module_dir / "data"
    data_dir.mkdir(parents=True)
    (module_dir / "config.yaml").write_text(
        "\n".join(
            [
                f"name: {module_name}",
                f"version: {version}",
                "modules: []",
                "depends_on: []",
                "data:",
                "  dirs:",
                "    - ./data",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_dir / "units.yaml").write_text(
        "- model: unit\n  name: custom_unit\n  abbreviation: cu\n",
        encoding="utf-8",
    )


def _bootstrap_args(registry: Path, *extra: str) -> list[str]:
    return ["bootstrap", "--registry", str(registry), *extra]


def test_bootstrap_registers_and_validates_the_packaged_catalog(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = tmp_path / "terminology" / "registry.json"

    assert main(_bootstrap_args(registry)) == 0

    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert stat.S_IMODE(registry.stat().st_mode) == 0o600
    assert payload["active"] == {
        "module_name": "star_upper_gi",
        "version": "0.1.2",
    }
    assert set(payload["modules"]) == set(PACKAGED_KNOWLEDGE_BASE_MODULES)
    for module_name in PACKAGED_KNOWLEDGE_BASE_MODULES:
        descriptor = get_packaged_knowledge_base(module_name)
        entry = payload["modules"][descriptor.module_name][descriptor.version]
        assert entry["sources"] == [
            {
                "kind": "provider",
                "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                "content_sha256": descriptor.content_sha256,
            }
        ]

    event = json.loads(capsys.readouterr().out)
    assert event == {
        "event": "lx_dtypes.knowledge_base_bootstrap",
        "module": "star_upper_gi",
        "registry": str(registry),
        "status": "ok",
        "version": "0.1.2",
    }


def test_bootstrap_uses_environment_registry_and_requested_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry = tmp_path / "registry.json"
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry))

    assert main(["bootstrap", "--module", "dgvs_reporting"]) == 0

    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert payload["active"] == {
        "module_name": "dgvs_reporting",
        "version": "0.1.0",
    }


def test_bootstrap_preserves_custom_active_identity(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    custom_root = tmp_path / "custom-bundles"
    _write_custom_bundle(custom_root)
    registry.write_text(
        json.dumps(
            {
                "active": {
                    "module_name": "custom_reporting",
                    "version": "7.4.0",
                },
                "modules": {
                    "custom_reporting": {
                        "7.4.0": {"input_dirs": [str(custom_root)]},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(_bootstrap_args(registry)) == 0

    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert payload["active"] == {
        "module_name": "custom_reporting",
        "version": "7.4.0",
    }
    assert set(PACKAGED_KNOWLEDGE_BASE_MODULES).issubset(payload["modules"])


def test_bootstrap_activates_default_for_nonempty_registry_without_active(
    tmp_path: Path,
) -> None:
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "modules": {
                    "deployment_owned": {
                        "4.2.0": {"input_dirs": ["/deployment/terminology"]},
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    assert main(_bootstrap_args(registry)) == 0

    payload = json.loads(registry.read_text(encoding="utf-8"))
    descriptor = get_packaged_knowledge_base("star_upper_gi")
    assert payload["active"] == {
        "module_name": descriptor.module_name,
        "version": descriptor.version,
    }
    assert "deployment_owned" in payload["modules"]


@pytest.mark.parametrize(
    "stale_entry",
    [
        {
            "sources": [
                {
                    "kind": "provider",
                    "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                    "content_sha256": "0" * 64,
                }
            ]
        },
        {"input_dirs": ["/removed-venv/site-packages/lx_dtypes/data"]},
        {
            "sources": [
                {
                    "kind": "filesystem",
                    "input_dirs": ["/removed-venv/site-packages/lx_dtypes/data"],
                }
            ]
        },
    ],
)
def test_bootstrap_repairs_recognized_stale_packaged_entry(
    tmp_path: Path,
    stale_entry: dict[str, object],
) -> None:
    descriptor = get_packaged_knowledge_base("star_upper_gi")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "active": {
                    "module_name": descriptor.module_name,
                    "version": descriptor.version,
                },
                "modules": {
                    descriptor.module_name: {
                        descriptor.version: stale_entry,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(_bootstrap_args(registry)) == 0

    payload = json.loads(registry.read_text(encoding="utf-8"))
    source = payload["modules"][descriptor.module_name][descriptor.version]["sources"][
        0
    ]
    assert source["provider"] == BUILTIN_KNOWLEDGE_BASE_PROVIDER
    assert source["content_sha256"] == descriptor.content_sha256


def test_bootstrap_migrates_stale_active_packaged_version(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "active": {"module_name": "star_upper_gi", "version": "0.1.1"},
                "modules": {
                    "star_upper_gi": {
                        "0.1.1": {
                            "input_dirs": ["/removed-venv/site-packages/lx_dtypes/data"]
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(_bootstrap_args(registry)) == 0

    descriptor = get_packaged_knowledge_base("star_upper_gi")
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert payload["active"] == {
        "module_name": descriptor.module_name,
        "version": descriptor.version,
    }
    assert "0.1.1" not in payload["modules"]["star_upper_gi"]


def test_bootstrap_rejects_custom_packaged_identity_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    descriptor = get_packaged_knowledge_base("star_upper_gi")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "active": {
                    "module_name": descriptor.module_name,
                    "version": descriptor.version,
                },
                "modules": {
                    descriptor.module_name: {
                        descriptor.version: {
                            "sources": [
                                {
                                    "kind": "filesystem",
                                    "input_dirs": ["/deployment/owned"],
                                }
                            ]
                        }
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    original = registry.read_bytes()

    assert main(_bootstrap_args(registry)) == 1

    event = json.loads(capsys.readouterr().err)
    assert event["status"] == "error"
    assert "immutable knowledge-base identity collision" in event["detail"]
    assert registry.read_bytes() == original


def test_bootstrap_is_byte_idempotent(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    assert main(_bootstrap_args(registry)) == 0
    original = registry.read_bytes()

    assert main(_bootstrap_args(registry)) == 0

    assert registry.read_bytes() == original


def test_bootstrap_missing_packaged_module_fails_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = tmp_path / "registry.json"

    assert main(_bootstrap_args(registry, "--module", "missing_test_module")) == 1

    event = json.loads(capsys.readouterr().err)
    assert event["status"] == "error"
    assert not registry.exists()
