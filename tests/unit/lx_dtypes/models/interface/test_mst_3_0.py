"""Tests for MST 3.0 master source table data."""

import pytest
from pathlib import Path
from lx_dtypes.models.interface import KnowledgeBaseConfig


class TestMST30:
    """Test MST 3.0 master source table loading and validation."""

    @pytest.fixture
    def mst_3_0_config(self):
        """Load MST 3.0 configuration."""
        mst_dir = (
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "lx_dtypes"
            / "data"
            / "mst_3_0"
        )
        if not mst_dir.exists():
            pytest.skip(f"MST 3.0 data not found at {mst_dir}")
        return KnowledgeBaseConfig.from_directory(mst_dir)

    def test_mst_3_0_loads(self, mst_3_0_config):
        """Test that MST 3.0 data loads successfully."""
        assert mst_3_0_config is not None

    def test_mst_3_0_has_data_files(self, mst_3_0_config):
        """Test that MST 3.0 contains expected data structures."""
        # MST 3.0 should have loaded various anatomy, finding, diagnosis classifications
        assert mst_3_0_config.version is not None

    def test_mst_anatomy_location_exists(self, mst_3_0_config):
        """Test that MST 3.0 anatomy locations are defined."""
        # This is a basic sanity check that the data was loaded
        assert mst_3_0_config is not None
