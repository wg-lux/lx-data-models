from __future__ import annotations

import pytest

from lx_dtypes.scripts.verify_packaged_report_templates import (
    REQUIRED_PACKAGED_REPORT_TEMPLATES,
    verify_packaged_report_templates,
)


def test_multiple_packaged_report_templates_are_published_and_usable() -> None:
    assert verify_packaged_report_templates() == list(
        REQUIRED_PACKAGED_REPORT_TEMPLATES
    )


def test_packaged_report_template_verifier_requires_multiple_templates() -> None:
    with pytest.raises(ValueError, match="At least two"):
        verify_packaged_report_templates(["upper_gi_quality_2025"])
