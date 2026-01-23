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
    """
    Create a sample ClassificationChoiceDescriptor pydantic model configured for a numeric distribution.

    Parameters:
        unit_fixture (Unit): Unit model whose name will be assigned to the descriptor's `unit` field.

    Returns:
        ClassificationChoiceDescriptor: A pydantic model named "Sample Descriptor" with type `NUMERIC`, a `NORMAL` numeric distribution, and numeric distribution parameters (`mean`: 0.0, `stddev`: 1.0).
    """
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
    """
    Create and return a ClassificationChoiceDescriptorDjango instance synchronized from a pydantic ClassificationChoiceDescriptor.

    Parameters:
        classification_choice_descriptor_fixture (ClassificationChoiceDescriptor): Pydantic model describing the classification choice descriptor to sync.
        django_unit_fixture (UnitDjango): Django Unit fixture whose database state will be refreshed before syncing.

    Returns:
        ClassificationChoiceDescriptorDjango: Django model instance created or updated from the pydantic model's ddict.
    """
    django_unit_fixture.refresh_from_db()

    classification_choice_descriptor_django = (
        ClassificationChoiceDescriptorDjango.sync_from_ddict(
            classification_choice_descriptor_fixture.ddict
        )
    )

    return classification_choice_descriptor_django
