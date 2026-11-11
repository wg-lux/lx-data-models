"""Architecture checks run without importing the library's runtime model graph."""

from pathlib import Path

import pytest
import yaml

from scripts.lint_model_boundaries import BoundaryInventory, check, inventory
from tests.paths import REPOSITORY_ROOT


def policy() -> BoundaryInventory:
    return BoundaryInventory(
        version=1,
        extra_field_exceptions=[],
        contract_runtime_dependencies=[],
        framework_adapters=[],
    )


def test_repository_model_boundaries():
    document = yaml.safe_load(
        (REPOSITORY_ROOT / "docs/model-boundaries.yml").read_text()
    )
    assert check(REPOSITORY_ROOT, BoundaryInventory.model_validate(document)) == []
    assert not list((REPOSITORY_ROOT / "lx_dtypes").rglob("test_*.py"))
    assert not list((REPOSITORY_ROOT / "lx_dtypes").rglob("conftest.py"))


@pytest.mark.parametrize(
    "base, imports",
    [
        ("BaseModel", "from pydantic import BaseModel"),
        ("Model", "from pydantic import BaseModel as Model"),
        ("pyd.BaseModel", "import pydantic as pyd"),
        ("RootModel[int]", "from pydantic import RootModel"),
    ],
)
def test_direct_pydantic_bases_are_rejected(tmp_path: Path, base: str, imports: str):
    package = tmp_path / "lx_dtypes"
    package.mkdir()
    (package / "model.py").write_text(f"{imports}\nclass Bypass({base}):\n    pass\n")
    assert any("bypasses shared policy" in issue for issue in check(tmp_path, policy()))


def test_runtime_dependencies_include_deferred_imports_but_not_annotations(
    tmp_path: Path,
):
    package = tmp_path / "lx_dtypes/models/contracts"
    package.mkdir(parents=True)
    (package / "example.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n    from lx_dtypes.models.ledger import Ledger\n"
        "def evaluate():\n    from lx_dtypes.evaluation import validate_contract\n"
    )
    _, _, dependencies, _ = inventory(tmp_path)
    assert dependencies == {
        ("lx_dtypes/models/contracts/example.py", "lx_dtypes.evaluation")
    }
    assert any(
        "Unreviewed contract runtime dependency" in issue
        for issue in check(tmp_path, policy())
    )


def test_extra_policy_and_framework_exceptions_require_review(tmp_path: Path):
    package = tmp_path / "lx_dtypes"
    package.mkdir()
    (package / "adapter.py").write_text(
        "from ninja import Schema\nfrom pydantic import ConfigDict\n"
        "class Adapter(Schema):\n    model_config = ConfigDict(extra='allow')\n"
    )
    findings = check(tmp_path, policy())
    assert any("Unreviewed extra-field exception" in finding for finding in findings)
    assert any("Unreviewed framework adapter" in finding for finding in findings)
