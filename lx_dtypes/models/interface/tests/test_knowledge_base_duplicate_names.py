from __future__ import annotations

from pathlib import Path

import pytest

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig


def test_create_from_config_rejects_duplicate_model_names(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    records_file = tmp_path / "records.yaml"

    config_file.write_text(
        (
            "name: duplicate_module\n"
            "version: \"1.0.0\"\n"
            "data:\n"
            "  files:\n"
            "    - records.yaml\n"
        ),
        encoding="utf-8",
    )
    records_file.write_text(
        (
            "- model: finding\n"
            "  name: duplicate_finding\n"
            "- model: finding\n"
            "  name: duplicate_finding\n"
        ),
        encoding="utf-8",
    )

    config = KnowledgeBaseConfig.from_yaml_file(config_file)
    config.normalize_data_paths(config_file)

    with pytest.raises(ValueError) as exc_info:
        KnowledgeBase.create_from_config(config)

    err = str(exc_info.value)
    assert "Duplicate 'finding' name 'duplicate_finding'" in err
    assert ":1:3" in err
    assert ":3:3" in err
