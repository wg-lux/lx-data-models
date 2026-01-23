from typing import List, Literal, Union, cast

from .knowledge_base import (
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    # KB_MODELS,
    # KB_MODELS_DJANGO,
    KnowledgeBaseModelsDjangoLookupType,
    KnowledgeBaseModelsLookupType,
    knowledge_base_models_django_lookup,
    knowledge_base_models_lookup,
)
from .ledger import (
    # L_DDICTS,
    L_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_ORDERED,
    # L_MODELS,
    # L_MODELS_DJANGO,
    LedgerModelsDjangoLookupType,
    LedgerModelsLookupType,
    ledger_models_django_lookup,
    ledger_models_lookup,
)


class ModelsLookupType(
    KnowledgeBaseModelsLookupType,
    LedgerModelsLookupType,
):
    pass


models_lookup = ModelsLookupType(
    **knowledge_base_models_lookup,
    **ledger_models_lookup,
)


class ModelsDjangoLookupType(
    KnowledgeBaseModelsDjangoLookupType,
    LedgerModelsDjangoLookupType,
):
    pass


models_django_lookup: ModelsDjangoLookupType = ModelsDjangoLookupType(
    **knowledge_base_models_django_lookup,
    **ledger_models_django_lookup,
)

MODEL_NAMES_LITERAL = Union[
    KB_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_LITERAL,
]

MODEL_NAMES: List[MODEL_NAMES_LITERAL] = KB_MODEL_NAMES_ORDERED + L_MODEL_NAMES_ORDERED


def get_model_pk_field(model_name: MODEL_NAMES_LITERAL) -> Literal["name", "uuid"]:
    """
    Get the primary-key field name used by the specified model ('name' or 'uuid').

    Parameters:
        model_name (MODEL_NAMES_LITERAL): The model identifier to look up.

    Returns:
        pk (Literal['name', 'uuid']): `'name'` if the model's primary key field is name, `'uuid'` if it is uuid.

    Raises:
        ValueError: If `model_name` is not present in the models lookup.
    """
    if model_name not in models_django_lookup:
        raise ValueError(f"Model name '{model_name}' is not recognized.")
    model = models_django_lookup[model_name]  # type: ignore[literal-required]
    pk = cast(Literal["name", "uuid"], model.ddict_pk_field_name())
    assert pk in ("name", "uuid")

    return pk


__all__ = [
    "MODEL_NAMES",
    "ModelsDjangoLookupType",
    "ModelsLookupType",
    "models_django_lookup",
    "models_lookup",
    "MODEL_NAMES_LITERAL",
    "get_model_pk_field",
]
