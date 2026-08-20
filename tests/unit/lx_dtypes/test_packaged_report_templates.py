from __future__ import annotations

import pytest

from lx_dtypes.scripts import verify_packaged_report_templates as verifier_module
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


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "",
                "report_sections": [{"title_de": "Befund"}],
            },
            "no German title",
        ),
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "Koloskopie",
                "report_sections": [],
            },
            "no report sections",
        ),
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "Koloskopie",
                "report_sections": [{"title_de": ""}],
            },
            "unlabeled German section",
        ),
    ],
)
def test_packaged_report_template_verifier_rejects_incomplete_german_demo(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    message: str,
) -> None:
    class _KnowledgeBase:
        def export_report_template(self, template_name: str) -> dict[str, object]:
            del template_name
            return payload

    class _Loader:
        def load_knowledge_base(self, module_name: str) -> _KnowledgeBase:
            assert module_name == "report_template_examples"
            return _KnowledgeBase()

    monkeypatch.setattr(verifier_module, "DataLoader", _Loader)

    with pytest.raises(RuntimeError, match=message):
        verify_packaged_report_templates(["template_a", "template_b"])
