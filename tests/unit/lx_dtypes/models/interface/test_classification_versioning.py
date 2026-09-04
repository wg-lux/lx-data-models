"""Tests for classification versioning functionality.

Demonstrates how to load and use different versions of classifications
that may evolve over time to reflect updated clinical guidelines.
"""

import pytest
from pathlib import Path
from lx_dtypes.models.interface import KnowledgeBaseConfig


class TestClassificationVersioning:
    """Test classification versioning functionality."""

    @pytest.fixture
    def classification_v1_legacy(self):
        """Load the legacy version of polyp size classification."""
        demo_dir = (
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "demo-data"
            / "classification_versioning"
            / "polyp_size_category_v1_legacy"
        )
        if not demo_dir.exists():
            pytest.skip(f"Demo data not found at {demo_dir}")
        return KnowledgeBaseConfig.from_directory(demo_dir)

    @pytest.fixture
    def classification_v2_esge2024(self):
        """Load the ESGE 2024 version of polyp size classification."""
        demo_dir = (
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "demo-data"
            / "classification_versioning"
            / "polyp_size_category_v2_esge2024"
        )
        if not demo_dir.exists():
            pytest.skip(f"Demo data not found at {demo_dir}")
        return KnowledgeBaseConfig.from_directory(demo_dir)

    def test_legacy_version_loads(self, classification_v1_legacy):
        """Test that legacy version loads correctly."""
        assert classification_v1_legacy is not None
        assert classification_v1_legacy.name == "polyp_size_category_v1_legacy"
        assert classification_v1_legacy.version == "1.0.0"

    def test_esge2024_version_loads(self, classification_v2_esge2024):
        """Test that ESGE 2024 version loads correctly."""
        assert classification_v2_esge2024 is not None
        assert classification_v2_esge2024.name == "polyp_size_category_v2_esge2024"
        assert classification_v2_esge2024.version == "2.0.0"

    def test_versions_are_different(self, classification_v1_legacy, classification_v2_esge2024):
        """Test that the two versions are distinct."""
        assert classification_v1_legacy.name != classification_v2_esge2024.name
        assert classification_v1_legacy.version != classification_v2_esge2024.version
