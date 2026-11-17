"""The single rule binding a ledger observation to its exact KB definition."""

from typing import Protocol

from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.validation import SemanticValidationError


class KbDefinition(Protocol):
    """Any KB record: identified by its name within its owning module."""

    @property
    def name(self) -> str: ...

    @property
    def kb_module_name(self) -> str: ...


def ensure_pinned_definition(
    *,
    name: str,
    module: str,
    version: str,
    definition: KbDefinition,
    identity: KnowledgeBaseIdentity,
    label: str,
) -> None:
    """Require the observation's name, module and version to match exactly.

    ``identity`` is the resolved version of ``definition``'s owning module.
    """
    if (
        name != definition.name
        or module != definition.kb_module_name
        or module != identity.knowledge_base_module
        or version != identity.knowledge_base_version
    ):
        raise SemanticValidationError(
            "terminology.identity_mismatch",
            f"{label} must match its exact KB definition identity",
        )


__all__ = ["KbDefinition", "ensure_pinned_definition"]
