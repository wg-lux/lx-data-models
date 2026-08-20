from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import KnowledgeBaseIdentity


def test_knowledge_base_identity_has_stable_frontend_representation() -> None:
    identity = KnowledgeBaseIdentity.model_validate(
        {
            "knowledge_base_module": " report_template_examples ",
            "knowledge_base_version": " 0.1.0 ",
        }
    )

    assert identity.knowledge_base_module == "report_template_examples"
    assert identity.knowledge_base_version == "0.1.0"
    assert identity.canonical_name == "report_template_examples@0.1.0"
    assert identity.model_dump(mode="json") == {
        "knowledge_base_module": "report_template_examples",
        "knowledge_base_version": "0.1.0",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"knowledge_base_module": "", "knowledge_base_version": "0.1.0"},
        {
            "knowledge_base_module": "report_template_examples",
            "knowledge_base_version": "",
        },
        {
            "knowledge_base_module": "report_template_examples@0.1.0",
            "knowledge_base_version": "0.1.0",
        },
        {
            "knowledge_base_module": "report_template_examples",
            "knowledge_base_version": "0.1.0",
            "unexpected": True,
        },
    ],
)
def test_knowledge_base_identity_rejects_ambiguous_payloads(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        KnowledgeBaseIdentity.model_validate(payload)
