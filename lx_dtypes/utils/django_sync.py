from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from lx_dtypes.models.interface.DbInterface import DbInterface
    from lx_dtypes.models.knowledge_base.main import (
        KB_MODEL_NAMES_LITERAL,
        # KB_MODEL_NAMES_ORDERED,
        KB_MODELS,
        # knowledge_base_models_django_lookup,
    )


def sort_kb_model_entries_by_load_order(
    entries: List[Tuple["KB_MODEL_NAMES_LITERAL", "KB_MODELS"]],
) -> list[tuple["KB_MODEL_NAMES_LITERAL", "KB_MODELS"]]:
    from lx_dtypes.models.knowledge_base.main import (
        KB_MODEL_NAMES_ORDERED,
    )

    order_index = {
        name: index for index, name in enumerate(iterable=KB_MODEL_NAMES_ORDERED)
    }
    module_entries_sorted = sorted(
        entries, key=lambda x: order_index.get(x[0], len(KB_MODEL_NAMES_ORDERED))
    )
    return module_entries_sorted


def sync_django_db_from_interface(db_interface: "DbInterface") -> None:
    """Sync the Django database from the given DbInterface instance."""
    from lx_dtypes.models.knowledge_base.main import (
        knowledge_base_models_django_lookup,
    )

    kb = db_interface.knowledge_base
    kb_entries_by_module_name = kb.kb_entries_by_module_name()

    kb_config = kb.config

    ordered_module_names = kb_config.modules

    for module_name in ordered_module_names:
        print(f"Syncing module: {module_name}")
        assert module_name in kb_entries_by_module_name
        module_entries = kb_entries_by_module_name[module_name]
        module_entries_sorted = sort_kb_model_entries_by_load_order(
            entries=module_entries,
        )

        for model_name, model_instance in module_entries_sorted:
            django_type = knowledge_base_models_django_lookup[model_name]
            model_ddict = model_instance.ddict
            try:
                django_type.sync_from_ddict(model_ddict)  # type: ignore
            except Exception as e:
                print(
                    f"Error syncing {model_name} with name {model_instance.name}: {e}"
                )
                print(model_ddict)
                raise e
