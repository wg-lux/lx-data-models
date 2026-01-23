from pytest import fixture

from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDjango import UnitDjango
from lx_dtypes.names import (
    ClassificationChoiceDescriptorTypes,
    NumericDistributionChoices,
)

from ..ClassificationChoiceDescriptor import ClassificationChoiceDescriptor
from ..ClassificationChoiceDescriptorDjango import (
    ClassificationChoiceDescriptorDjango,
)


@fixture(scope="session")
def classification_choice_descriptor_fixture(
    unit_fixture: Unit,
) -> ClassificationChoiceDescriptor:
    pydantic_model = ClassificationChoiceDescriptor(
        name="Sample Descriptor",
        classification_choice_descriptor_type=ClassificationChoiceDescriptorTypes.NUMERIC,
        numeric_distribution=NumericDistributionChoices.NORMAL,
        numeric_distribution_params={"mean": 0.0, "stddev": 1.0},
        unit=unit_fixture.name,
    )

    return pydantic_model


@fixture()
def django_classification_choice_descriptor_fixture(
    classification_choice_descriptor_fixture: ClassificationChoiceDescriptor,
    django_unit_fixture: UnitDjango,
) -> "ClassificationChoiceDescriptorDjango":
    django_unit_fixture.refresh_from_db()

    classification_choice_descriptor_django = (
        ClassificationChoiceDescriptorDjango.sync_from_ddict(
            classification_choice_descriptor_fixture.ddict
        )
    )

    return classification_choice_descriptor_django
