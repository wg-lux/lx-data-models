"""Combined model names and types without loading backend adapters."""

from .knowledge_base.pydantic_main import (
    KB_DDICTS,
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
)
from .ledger.pydantic_main import (
    L_DDICTS,
    L_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_ORDERED,
    L_MODELS,
)

type MODEL_NAMES_LITERAL = KB_MODEL_NAMES_LITERAL | L_MODEL_NAMES_LITERAL
MODEL_NAMES = KB_MODEL_NAMES_ORDERED + L_MODEL_NAMES_ORDERED
type MODELS = KB_MODELS | L_MODELS
type DDICTS = KB_DDICTS | L_DDICTS

__all__ = ["DDICTS", "MODEL_NAMES", "MODEL_NAMES_LITERAL", "MODELS"]
