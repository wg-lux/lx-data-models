"""Load packaged, data-only suggestions for reviewed table import mappings."""

from typing import TYPE_CHECKING, cast

import yaml

from lx_dtypes.models.contracts.table_import import (
    TableConceptVocabulary,
    TableImportVocabulary,
)
from lx_dtypes.models.knowledge_base.pydantic_main import KB_MODELS
from lx_dtypes.utils.parser import camel_to_snake

from .data_roots import package_data_root

if TYPE_CHECKING:
    from .KnowledgeBase import KnowledgeBase


def load_table_import_vocabulary(
    knowledge_base: "KnowledgeBase | None" = None,
) -> TableImportVocabulary:
    """Expand authored labels only from the caller's selected knowledge base."""
    path = package_data_root() / "table_import_vocabulary.yml"
    vocabulary = TableImportVocabulary.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )
    if knowledge_base is not None:
        for concept_type in vocabulary.concept_models:
            records = cast(
                dict[str, KB_MODELS],
                getattr(knowledge_base, camel_to_snake(concept_type)),
            )
            for name, record in sorted(records.items()):
                terms = [
                    term
                    for term in (record.name_en, record.name_de)
                    if term.strip().casefold() != "unknown"
                ]
                terms.insert(0, record.name)
                terms.extend(
                    vocabulary.concept_aliases.get(concept_type, {}).get(name, [])
                )
                # Preserve a real 'unknown' concept, but not missing-label sentinels.
                aliases = {
                    term.strip().casefold(): term
                    for term in reversed(terms)
                    if term.strip()
                }
                vocabulary.concepts.append(
                    TableConceptVocabulary(
                        concept_type=concept_type,
                        name=name,
                        knowledge_base=knowledge_base.config.knowledge_base_identity,
                        source_module=record.kb_module_name,
                        aliases=list(aliases.values()),
                    )
                )
    return vocabulary
