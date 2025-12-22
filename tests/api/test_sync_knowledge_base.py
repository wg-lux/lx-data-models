from typing import Callable, List, Literal, Tuple

import pytest

from lx_dtypes.contrib.lx_django.parser.main import get_kb_django_model_by_name
from lx_dtypes.models.base_models.log import Log
from lx_dtypes.models.knowledge_base import DataLoader, KnowledgeBase
from lx_dtypes.typing.django.kb_models import KB_DJANGO_MODEL_BY_NAME
from lx_dtypes.typing.pydantic.knowledge_base_shallow import (
    KB_SHALLOW_UNION_PYDANTIC_LIST,
)

KB_MODEL_NAMES = Literal[
    "citation",
    "classification",
    "classification_type",
    "classification_choice",
    "classification_choice_descriptor",
    "examination",
    "examination_type",
    "finding",
    "finding_type",
    "indication",
    "indication_type",
    "intervention",
    "intervention_type",
    "unit",
    "unit_type",
]

MODEL_LOAD_ORDER: list[KB_MODEL_NAMES] = [
    "citation",
    "unit_type",
    "unit",
    "classification_choice_descriptor",
    "classification_choice",
    "classification_type",
    "classification",
    "finding_type",
    "finding",
    "intervention_type",
    "intervention",
    "indication_type",
    "indication",
    "examination_type",
    "examination",
]


def sort_kb_model_entries_by_load_order(
    entries: List[Tuple[str, "KB_SHALLOW_UNION_PYDANTIC_LIST"]],
) -> list[tuple[str, object]]:
    order_index = {name: index for index, name in enumerate(MODEL_LOAD_ORDER)}
    return sorted(entries, key=lambda x: order_index.get(x[0], len(MODEL_LOAD_ORDER)))


DJANGO_MODELS = KB_DJANGO_MODEL_BY_NAME.values()


# TODO add transform utils based on those tests
@pytest.mark.django_db
class TestSyncKnowledgeBase:
    def test_get_dependency_graph(
        self,
        yaml_data_loader: DataLoader,
        lx_knowledge_base: KnowledgeBase,
        log_writer: Callable[..., Log],
    ) -> None:
        kb = lx_knowledge_base
        kb_entries_by_module_name = kb.kb_entries_by_module_name()

        kb_config = kb.config
        assert kb_config is not None

        ordered_module_names = kb_config.modules

        for module_name in ordered_module_names:
            assert module_name in kb_entries_by_module_name
            module_entries = kb_entries_by_module_name[module_name]
            module_entries = sort_kb_model_entries_by_load_order(module_entries)
            for model_name, entry in module_entries:
                # _skip = [  # TODO properly implement information source model
                #     "information_source",
                # ]
                # if model_name in _skip:
                #     continue

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

        # for module_name, entries in kb_entries_by_module_name.items():
        #     log_writer(
        #         f"Module '{module_name}' has {len(entries)} entries.",
        #         context={"module_name": module_name, "entry_count": str(len(entries))},
        #     )
