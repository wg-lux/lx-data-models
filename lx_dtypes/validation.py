"""Compatibility exports for the canonical lx_dtypes.evaluation boundary."""

from lx_dtypes.evaluation import (
    assess_examination,
    validate_contract,
    validate_contract_json,
)
from lx_dtypes.models.contracts.validation import (
    ContractValidationResult,
    ValidationIssue,
    ValidationReport,
)

__all__ = [
    "ContractValidationResult",
    "ValidationIssue",
    "ValidationReport",
    "assess_examination",
    "validate_contract",
    "validate_contract_json",
]
