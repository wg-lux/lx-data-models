"""Keep the data-model concept map's contract-family table in sync with the code."""

import re

from tests.paths import PACKAGE_ROOT, REPOSITORY_ROOT

CONCEPT_MAP = REPOSITORY_ROOT / "docs/guides/data-model-concept-map.md"


def _contract_modules() -> set[str]:
    contracts = PACKAGE_ROOT / "models/contracts"
    modules = {path.stem for path in contracts.glob("*.py")}
    packages = {path.name for path in contracts.iterdir() if path.is_dir()}
    return {name for name in modules | packages if not name.startswith("_")}


def _documented_modules() -> list[str]:
    text = CONCEPT_MAP.read_text(encoding="utf-8")
    level_5 = text.split("## Level 5", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in level_5.splitlines() if line.startswith("| ")][1:]
    return [
        name
        for row in rows
        for name in re.findall(r"`([a-z_0-9]+)`", row.split("|")[2])
    ]


def test_every_contract_module_is_mapped_to_exactly_one_family() -> None:
    documented = _documented_modules()
    assert len(documented) == len(set(documented)), "module listed twice"
    assert set(documented) == _contract_modules()
