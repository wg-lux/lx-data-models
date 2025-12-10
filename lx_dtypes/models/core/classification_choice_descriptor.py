from typing import Optional

from lx_dtypes.models.core.unit import Unit
from lx_dtypes.models.shallow.classification_choice_descriptor import (
    ClassificationChoiceDescriptorShallow,
)


class ClassificationChoiceDescriptor(ClassificationChoiceDescriptorShallow):
    unit: Optional[Unit]
