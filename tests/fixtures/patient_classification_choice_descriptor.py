from lx_dtypes.lx_django.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor as DjangoClassificationChoiceDescriptorModel,
)
from lx_dtypes.lx_django.models.core.unit import (
    Unit as DjangoUnitModel,
)
from pytest import fixture

from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.core.unit import Unit


@fixture(scope="session")
def sample_classification_choice_descriptor_numeric(
    sample_unit: Unit,
) -> ClassificationChoiceDescriptor:
    classification_choice_descriptor = ClassificationChoiceDescriptor(
        descriptor_type="numeric",
        name="Sample Numeric Descriptor",
        tags=[],
        unit=sample_unit,
    )

    return classification_choice_descriptor


@fixture(scope="function")
def sample_django_classification_choice_descriptor_numeric(
    sample_classification_choice_descriptor_numeric: ClassificationChoiceDescriptor,
    sample_django_unit: DjangoUnitModel,
) -> DjangoClassificationChoiceDescriptorModel:
    ddict = sample_classification_choice_descriptor_numeric.to_ddict_shallow()
    django_classification_choice_descriptor = (
        DjangoClassificationChoiceDescriptorModel.sync_from_ddict_shallow(ddict)
    )

    django_classification_choice_descriptor.refresh_from_db()
    return django_classification_choice_descriptor
