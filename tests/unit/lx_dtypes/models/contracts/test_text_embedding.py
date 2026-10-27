import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.text_embedding import (
    EmbeddingSpace,
    ReportConceptSpan,
    TextEmbedding,
)


def test_cosine_requires_identical_vector_spaces() -> None:
    space = EmbeddingSpace(
        model="local", revision="1", dimensions=2, preprocessing="none"
    )
    left = TextEmbedding(space=space, vector=[1.0, 0.0])
    assert left.cosine(left) == 1.0
    assert left.cosine(TextEmbedding(space=space, vector=[0.0, 1.0])) == 0.0
    with pytest.raises(ValueError, match="different embedding spaces"):
        left.cosine(
            TextEmbedding(
                space=space.model_copy(update={"revision": "2"}), vector=[1.0, 0.0]
            )
        )


def test_span_does_not_accept_text_or_vectors() -> None:
    valid = {
        "report_id": 1,
        "source_hash": "a" * 64,
        "start": 0,
        "end": 5,
        "concept_kind": "finding",
        "annotation_id": 2,
    }
    assert ReportConceptSpan.model_validate(valid).end == 5
    for extra in ({"text": "arbitrary input"}, {"vector": [1.0]}):
        with pytest.raises(ValidationError):
            ReportConceptSpan.model_validate({**valid, **extra})
