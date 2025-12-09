from pathlib import Path

import yaml

from lx_dtypes.models.knowledge_base import KnowledgeBase


def export_knowledge_base(
    kb: KnowledgeBase, export_dir: Path, filename: str = "knowledge_base"
) -> None:
    """Export the knowledge base to the specified directory in YAML format.

    Args:
        kb (KnowledgeBase): The knowledge base to export.
        export_dir (Path): The directory to export the knowledge base to.
    """
    dump = kb.model_dump()
    export_path = export_dir / f"{filename}.yaml"

    with open(export_path, "w", encoding="utf-8") as f:
        yaml.dump(dump, f)
