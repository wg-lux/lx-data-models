from pytest import fixture

from lx_dtypes.models.core.classification import Classification, ClassificationType
from lx_dtypes.models.core.classification_choice import ClassificationChoice
from lx_dtypes.contrib.lx_django.models.core.classification_choice import (
    ClassificationChoice as DjangoClassificationChoiceModel,
)
from lx_dtypes.contrib.lx_django.models.core.classification import (
    Classification as DjangoClassificationModel,
    ClassificationType as DjangoClassificationTypeModel,
)


@fixture
def sample_classification_type() -> ClassificationType:
    return ClassificationType(
        name="Sample Classification Type",
        description="A sample classification type for testing.",
    )


@fixture(scope="function")
def sample_django_classification_type(
    sample_classification_type: ClassificationType,
) -> DjangoClassificationTypeModel:
    ddict = sample_classification_type.to_ddict_shallow()
    django_classification_type = DjangoClassificationTypeModel.sync_from_ddict_shallow(
        ddict
    )

    django_classification_type.refresh_from_db()
    return django_classification_type


@fixture
def sample_classification(
    sample_classification_type: ClassificationType,
    sample_classification_choice: ClassificationChoice,
) -> Classification:
    classification_choice_name = sample_classification_choice.name
    classification_type_name = sample_classification_type.name
    return Classification(
        name="Sample Classification",
        description="A sample classification for testing.",
        types={classification_type_name: sample_classification_type},
        classification_choices={
            classification_choice_name: sample_classification_choice
        },
    )


@fixture(scope="function")
def sample_django_classification(
    sample_classification: Classification,
    sample_django_classification_type: DjangoClassificationTypeModel,
    sample_django_classification_choice: DjangoClassificationChoiceModel,
) -> DjangoClassificationModel:
    ddict = sample_classification.to_ddict_shallow()
    django_classification = DjangoClassificationModel.sync_from_ddict_shallow(ddict)

    django_classification.refresh_from_db()
    return django_classification
