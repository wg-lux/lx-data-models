"""Illustrative example of classification versioning.

This example demonstrates how the same clinical measurement (polyp size in
millimeters) is assigned to different categorical bins by two different
classification versions, representing how clinical guidelines evolve over time.

The two versions shown here are:
  1. A legacy/hypothetical simpler binary scheme (polyp_size_category_v1_legacy)
  2. The current ESGE 2024 colorectal polypectomy/EMR guideline scheme
     (polyp_size_category_v2_esge2024)

Both versions use the same underlying raw measurement but differ in their
categorization logic and associated clinical recommendations.
"""

from pathlib import Path
from lx_dtypes.models.interface import KnowledgeBaseConfig
from lx_dtypes.models.interface.examples import example_mst_3_0

# Locate the demo data directory
demo_data_root = Path(__file__).parent.parent.parent.parent / "demo-data" / "classification_versioning"


def load_classification_version(version_name: str) -> KnowledgeBaseConfig:
    """Load a specific classification version.

    Args:
        version_name: Either 'polyp_size_category_v1_legacy' or
                     'polyp_size_category_v2_esge2024'

    Returns:
        A KnowledgeBaseConfig instance for that version.
    """
    version_dir = demo_data_root / version_name
    config = KnowledgeBaseConfig.from_directory(version_dir)
    return config


if __name__ == "__main__":
    # Load both versions
    legacy = load_classification_version("polyp_size_category_v1_legacy")
    esge2024 = load_classification_version("polyp_size_category_v2_esge2024")

    print("Classification Versioning Example")
    print("="*50)

    print(f"\nLegacy version: {legacy.name}")
    print(f"  Description: {legacy.description[:100]}...")

    print(f"\nCurrent version: {esge2024.name}")
    print(f"  Description: {esge2024.description[:100]}...")

    print("\nBoth versions classify the same raw measurement (polyp size in mm)")
    print("but with different category structures and clinical implications.")
