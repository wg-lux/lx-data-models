from typing import List, Tuple

from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.typing.django.kb_models import (
    KB_DJANGO_MODEL_BY_NAME,
    KB_UNION_DJANGO_MODEL_TYPE_LIST,
)
from lx_dtypes.typing.helper import KB_MODEL_NAMES_LITERAL, KB_MODEL_NAMES_ORDERED
from lx_dtypes.typing.pydantic.knowledge_base_shallow import (
    KB_SHALLOW_UNION_PYDANTIC_LIST,
)


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


def sort_kb_model_entries_by_load_order(
    entries: List[Tuple[KB_MODEL_NAMES_LITERAL, "KB_SHALLOW_UNION_PYDANTIC_LIST"]],
) -> list[tuple[KB_MODEL_NAMES_LITERAL, "KB_SHALLOW_UNION_PYDANTIC_LIST"]]:
    order_index = {name: index for index, name in enumerate(KB_MODEL_NAMES_ORDERED)}
    module_entries_sorted = sorted(
        entries, key=lambda x: order_index.get(x[0], len(KB_MODEL_NAMES_ORDERED))
    )
    return module_entries_sorted


def sync_django_db_from_knowledge_base(kb: KnowledgeBase) -> None:
    """Sync the Django database from the knowledge base."""
    kb_entries_by_module_name = kb.kb_entries_by_module_name()

    kb_config = kb.config
    assert kb_config is not None

    ordered_module_names = kb_config.modules

    for module_name in ordered_module_names:
        assert module_name in kb_entries_by_module_name

        module_entries = kb_entries_by_module_name[module_name]
        module_entries_sorted = sort_kb_model_entries_by_load_order(module_entries)

        for model_name, entry in module_entries_sorted:
            django_model_class = get_kb_django_model_by_name(model_name)
            assert django_model_class is not None

            try:
                _obj = django_model_class.sync_from_ddict_shallow(
                    entry.to_ddict_shallow()  # type: ignore
                )

            except Exception as e:
                object_repr = repr(entry)
                raise AssertionError(
                    f"Failed to sync model '{model_name}' from ddict shallow: {object_repr}"
                ) from e
