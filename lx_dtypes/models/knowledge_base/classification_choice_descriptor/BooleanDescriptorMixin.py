from lx_dtypes.models.knowledge_base.classification_choice_descriptor.DescriptorTypeMixin import (
    DescriptorTypeMixin,
)


class BooleanDescriptorMixin(DescriptorTypeMixin):
    default_value_bool: bool = False
