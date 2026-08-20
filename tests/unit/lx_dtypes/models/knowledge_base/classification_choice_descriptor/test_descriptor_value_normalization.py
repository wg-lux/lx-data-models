import pytest

from lx_dtypes.models.knowledge_base.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.contracts import DescriptorValue as PublicDescriptorValue
from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.names import ClassificationChoiceDescriptorTypes


def descriptor(
    descriptor_type: ClassificationChoiceDescriptorTypes,
) -> ClassificationChoiceDescriptor:
    return ClassificationChoiceDescriptor(
        name=f"{descriptor_type.value}_descriptor",
        classification_choice_descriptor_type=descriptor_type,
    )


def test_descriptor_value_remains_available_from_contracts() -> None:
    assert PublicDescriptorValue is DescriptorValue


@pytest.mark.parametrize("value", ["false", " FALSE ", "0", "no", "off"])
def test_normalize_value_parses_false_boolean_strings(value: str) -> None:
    boolean_descriptor = descriptor(ClassificationChoiceDescriptorTypes.BOOLEAN)

    assert boolean_descriptor.normalize_value(value) is False


def test_normalize_value_cleans_selection_values() -> None:
    selection_descriptor = descriptor(ClassificationChoiceDescriptorTypes.SELECTION)

    assert selection_descriptor.normalize_value([" first ", "", "second"]) == [
        "first",
        "second",
    ]


@pytest.mark.parametrize(
    ("descriptor_type", "value"),
    [
        (ClassificationChoiceDescriptorTypes.NUMERIC, ["1"]),
        (ClassificationChoiceDescriptorTypes.BOOLEAN, ["true"]),
    ],
)
def test_normalize_value_rejects_lists_for_scalar_descriptors(
    descriptor_type: ClassificationChoiceDescriptorTypes,
    value: list[str],
) -> None:
    scalar_descriptor = descriptor(descriptor_type)

    with pytest.raises(ValueError, match="List value is not supported"):
        scalar_descriptor.normalize_value(value)
