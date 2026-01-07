import pytest

from ..ClassificationChoice import ClassificationChoice


@pytest.fixture(scope="session")
def classification_choice_fixture() -> ClassificationChoice:
    return ClassificationChoice(
        name="sample_classification_choice",
        classification_choice_descriptors=["descriptor1", "descriptor2"],
        tags=["tag1", "tag2"],
    )
