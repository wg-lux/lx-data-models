"""Verify that the complete MST 3.0 data survives terminology merges."""

from pathlib import Path

import pytest

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def mst_3_0() -> KnowledgeBase:
    return load_knowledge_base(
        "mst_3_0",
        version="3.0.0",
        input_dirs=[ROOT / "lx_dtypes/data/mst_3_0"],
    )


def test_mst_3_0_loads(mst_3_0: KnowledgeBase) -> None:
    assert mst_3_0.config.name == "mst_3_0"
    assert mst_3_0.config.version == "3.0.0"
    mst_3_0.export_core_concepts()


def test_mst_3_0_has_complete_data(mst_3_0: KnowledgeBase) -> None:
    assert len(mst_3_0.finding) == 357
    assert len(mst_3_0.classification) == 39
    assert len(mst_3_0.classification_choice) == 285


def test_mst_anatomy_location_exists(mst_3_0: KnowledgeBase) -> None:
    assert "mst30_location_esophagus" in mst_3_0.classification
    assert "mst30_location_colon" in mst_3_0.classification
    assert "mst30_eus_other" in mst_3_0.finding
