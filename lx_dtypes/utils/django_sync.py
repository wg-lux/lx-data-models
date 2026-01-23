from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from django.db import models

from lx_dtypes.serialization import parse_str_list

if TYPE_CHECKING:
    from lx_dtypes.models.interface.DbInterface import DbInterface
    from lx_dtypes.models.knowledge_base.main import (
        KB_MODEL_NAMES_LITERAL,
        # KB_MODEL_NAMES_ORDERED,
        KB_MODELS,
        # knowledge_base_models_django_lookup,
    )


def parse_list_type_field(
    list_type_fields: List[str],
    m2m_field_names: set[str],
    defaults_dict: Dict[str, Any],
    instance: models.Model,
) -> None:
    for field_name in list_type_fields:
        if field_name in m2m_field_names:
            continue
        if field_name in defaults_dict:
            value = getattr(instance, field_name)
            if isinstance(value, str):
                value = [
                    item.strip()
                    for item in value.strip("[]").split(",")
                    if item.strip()
                ]
            setattr(instance, field_name, value)


def sync_from_ddict_m2m_field(
    m2m_values: Dict[str, object], instance: models.Model, cls: type[models.Model]
) -> None:
    for field_name, related_names in m2m_values.items():
        if related_names is None or related_names == "":
            continue

        # Normalize to a list of identifiers
        if isinstance(related_names, str):
            related_iterable = parse_str_list(related_names)
        elif isinstance(related_names, (list, tuple, set)):
            related_iterable = list(related_names)
        else:
            related_iterable = [related_names]  # type: ignore

        field = cls._meta.get_field(field_name)  # type: ignore
        related_model = field.related_model  # type: ignore

        related_instances = []
        for related_name in related_iterable:
            related_obj = related_model.objects.get(pk=related_name)  # type: ignore
            related_instances.append(related_obj)

        # Use the manager to set M2M relations; avoids direct assignment errors
        getattr(instance, field_name).set(related_instances)


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
