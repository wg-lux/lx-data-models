from .classification import KbClassificationLookupType, kb_classification_lookup


class KnowledgeBaseModelsLookupType(KbClassificationLookupType):
    pass


knowledge_base_models_lookup = KnowledgeBaseModelsLookupType(
    **kb_classification_lookup,
)
