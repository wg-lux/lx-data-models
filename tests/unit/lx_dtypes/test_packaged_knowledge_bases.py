from __future__ import annotations

from pathlib import Path

from lx_dtypes.knowledge_bases import (
    get_packaged_knowledge_base,
    list_packaged_knowledge_bases,
)


def test_catalog_exposes_verified_reporting_resources() -> None:
    descriptors = list_packaged_knowledge_bases()

    assert {(item.module_name, item.version) for item in descriptors} >= {
        ("dgvs_reporting", "0.1.0"),
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
    assert (data_root / descriptor.module_name / "config.yaml").is_file()
