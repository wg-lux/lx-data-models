import pytest

from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)

from ..Classification import Classification


@pytest.fixture(scope="session")
def classification_fixture(
    classification_choice_fixture: ClassificationChoice,
) -> Classification:
    return Classification(
        name="sample_classification",
        classification_choices=[classification_choice_fixture.name],
    )
