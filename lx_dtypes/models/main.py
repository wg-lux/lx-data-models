"""Backend aggregation reuses the canonical Pydantic model definitions."""

from .knowledge_base import KB_MODELS_DJANGO
from .ledger import L_MODELS_DJANGO
from .pydantic_main import DDICTS, MODEL_NAMES, MODEL_NAMES_LITERAL, MODELS

type MODELS_DJANGO = KB_MODELS_DJANGO | L_MODELS_DJANGO

__all__ = ["DDICTS", "MODEL_NAMES", "MODEL_NAMES_LITERAL", "MODELS", "MODELS_DJANGO"]
