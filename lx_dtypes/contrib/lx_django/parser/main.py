from ....typing.django.kb_models import (
    KB_DJANGO_MODEL_BY_NAME,
    KB_UNION_DJANGO_MODEL_TYPE_LIST,
)
from ....typing.helper import KB_MODEL_NAMES_LITERAL


def get_kb_django_model_by_name(
    name: KB_MODEL_NAMES_LITERAL,
) -> KB_UNION_DJANGO_MODEL_TYPE_LIST:
    """Get the Django model class for a given knowledge base model name.

    Args:
        name (str): The name of the knowledge base model.

    Returns:
        KB_UNION_DJANGO_MODEL_TYPE_LIST: The corresponding Django model class.

    Raises:
        KeyError: If the model name is not found in the mapping.
    """

    assert isinstance(name, str), "Model name must be a string."
    assert name in KB_DJANGO_MODEL_BY_NAME, f"Model name '{name}' not found."

    model = KB_DJANGO_MODEL_BY_NAME[name]

    return model
