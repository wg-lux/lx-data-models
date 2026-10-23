from __future__ import annotations

import ast
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models import contracts
from lx_dtypes.models.contracts.ai_dataset import (
    AIDataSetScoredActiveLearningCandidateContract,
    AIDataSetScoredActiveLearningCandidateContractContract,
)
from lx_dtypes.models.contracts.json_types import (
    VideoFrameCacheManifestLogPayload,
    VideoFrameCacheValidationLogPayload,
)
from lx_dtypes.models.contracts.video_frame_cache import (
    FrameCacheManifestLogPayload,
    FrameCacheValidationLogPayload,
)


def test_public_contract_exports_match_static_imports() -> None:
    tree = ast.parse(Path(contracts.__file__).read_text())
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1
    ]
    for node in imports:
        module = import_module(f"{contracts.__name__}.{node.module}")
        for alias in node.names:
            name = alias.asname or alias.name
            assert getattr(contracts, name) is getattr(module, alias.name)
            assert name in dir(contracts)
    assert set(contracts.__all__) <= set(dir(contracts))


@pytest.mark.parametrize(
    "statement",
    [
        "from lx_dtypes.models.contracts.text_detection import PixelBoundingBoxCore",
        "from lx_dtypes.models.contracts import KnowledgeBaseIdentity",
        "from lx_dtypes.models.contracts import validate_hub_transfer_video_payload",
        "from lx_dtypes.models.contracts.video_processing import VideoMaskConfig",
        "from lx_dtypes.models.contracts.aidataset_export import AIDataSetExportPayload",
    ],
)
def test_contract_imports_are_isolated_from_unrelated_domains(statement: str) -> None:
    script = f"""
import importlib.abc
import sys
class BlockHostImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {{'django', 'ninja', 'numpy', 'pandas', 'cv2', 'endoreg_db', 'lx_annotate', 'lx_anonymizer'}}:
            raise AssertionError(f"Unexpected host dependency: {{fullname}}")
sys.meta_path.insert(0, BlockHostImports())
{statement}
assert 'lx_dtypes.models.contracts.management_command' not in sys.modules
assert 'lx_dtypes.models.contracts.ai_dataset' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_legacy_scored_candidate_is_the_canonical_model() -> None:
    assert (
        AIDataSetScoredActiveLearningCandidateContractContract
        is AIDataSetScoredActiveLearningCandidateContract
    )
    payload = {
        "sample_index": 0,
        "video_id": 1,
        "frame_number": 2,
        "frame_id": 3,
        "timestamp": 0.1,
        "segment_id": 4,
        "probs": [0.5],
        "quality_score": 0.8,
        "uncertainty": 0.2,
        "diversity": 0.3,
        "rarity": 0.4,
        "quality_gate": 1.0,
        "frame_score": 0.9,
    }
    legacy = AIDataSetScoredActiveLearningCandidateContractContract.model_validate(
        payload
    )
    assert (
        AIDataSetScoredActiveLearningCandidateContract.model_validate(legacy) is legacy
    )
    assert legacy.model_dump() == payload
    with pytest.raises(ValidationError):
        AIDataSetScoredActiveLearningCandidateContractContract.model_validate(
            {**payload, "unknown": True}
        )


def test_cache_variants_preserve_wire_shape_and_mutability() -> None:
    mutable = FrameCacheManifestLogPayload(frame_dir="frames", file_count=2)
    frozen = VideoFrameCacheManifestLogPayload(frame_dir="frames", file_count=2)
    assert mutable.as_log_payload() == frozen.to_log_payload()
    assert "expected_count" not in mutable.as_log_payload()
    mutable.file_count = 3
    with pytest.raises(ValidationError, match="frozen"):
        frozen.file_count = 3
    other = FrameCacheManifestLogPayload(frame_dir="other", file_count=0)
    mutable.missing_frame_numbers.append(1)
    assert other.missing_frame_numbers == []
    assert frozen.missing_frame_numbers == []


def test_cache_validation_variants_preserve_required_count_and_strictness() -> None:
    mutable = FrameCacheValidationLogPayload(frame_dir="frames", file_count=0)
    assert mutable.db_extracted_frame_count == 0
    with pytest.raises(ValidationError, match="db_extracted_frame_count"):
        VideoFrameCacheValidationLogPayload(frame_dir="frames", file_count=0)  # type: ignore[call-arg]
    frozen = VideoFrameCacheValidationLogPayload(
        frame_dir="frames", file_count=0, db_extracted_frame_count=0
    )
    assert mutable.as_log_payload() == frozen.to_log_payload()
    for model in (FrameCacheValidationLogPayload, VideoFrameCacheValidationLogPayload):
        for extra in ({"unknown": True}, {"file_count": "0"}):
            with pytest.raises(ValidationError):
                model.model_validate(
                    {
                        "frame_dir": "frames",
                        "file_count": 0,
                        "db_extracted_frame_count": 0,
                        **extra,
                    }
                )
