"""Compatibility imports; implementation lives in lx_dtypes.models.knowledge_base.fhir.yaml."""

from lx_dtypes.models.knowledge_base.fhir.yaml import (
    FHIRPayload,
    fhir_to_yaml,
    knowledge_base_from_fhir,
    write_fhir_yaml,
)

__all__ = ["FHIRPayload", "fhir_to_yaml", "knowledge_base_from_fhir", "write_fhir_yaml"]
