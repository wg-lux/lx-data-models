from __future__ import annotations

from pathlib import Path

from lx_dtypes.knowledge_bases import (
    get_packaged_knowledge_base,
    list_packaged_knowledge_bases,
)


def test_catalog_exposes_verified_reporting_resources() -> None:
    descriptors = list_packaged_knowledge_bases()

    assert {(item.module_name, item.version) for item in descriptors} >= {
        ("coloreg", "0.1.0"),
        ("dgvs_reporting", "0.1.0"),
        ("dgvs_reporting", "0.2.0"),
        ("mst_3_0", "3.0.0"),
        ("star_upper_gi", "0.1.2"),
    }
    for descriptor in descriptors:
        resource = descriptor.verified_resource_directory()
        assert resource.joinpath("config.yaml").is_file()


def test_installed_wheel_data_root_is_runtime_only_and_loadable() -> None:
    descriptor = get_packaged_knowledge_base("star_upper_gi", "0.1.2")

    data_root = descriptor.installed_data_root()

    assert isinstance(data_root, Path)
    assert (
        data_root / "report_templates" / descriptor.module_name / "config.yaml"
    ).is_file()


def test_published_dgvs_reporting_release_is_retained_unchanged() -> None:
    """0.1.0 shipped in lx-dtypes 0.6.6; pinned examinations must still resolve it."""
    from lx_dtypes.models.interface.DataLoader import DataLoader

    retained = get_packaged_knowledge_base("dgvs_reporting", "0.1.0")
    assert retained.content_sha256 == (
        "3641cde9c205b1c57140613abc01fd6e4c83a176870aca0963b8554e6e8e07b5"
    )
    bundle = Path(str(retained.verified_resource_directory())).parent
    kb = DataLoader(input_dirs=[bundle]).load_knowledge_base("dgvs_reporting")
    assert kb.config.version == "0.1.0"
    sections = kb.report_template["colonoscopy_training_basic"].report_sections
    assert "report_electrosurgery" not in sections

    current = get_packaged_knowledge_base("dgvs_reporting", "0.2.0")
    assert current.default and not retained.default
