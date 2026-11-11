"""Contract parsing followed by explicit terminology and study evaluation.

Contracts own shapes and local invariants; these functions return findings and
delegate cross-model rules to their owning engines. No evaluation writes data.
"""

from typing import TYPE_CHECKING

from lx_dtypes.models.contracts.validation import (
    ContractValidationResult,
    ValidationIssue,
    ValidationReport,
)

from .contracts import (
    parse_contract,
    parse_contract_json,
    validate_contract,
    validate_contract_json,
)
from .examination import assess_examination

if TYPE_CHECKING:
    from .time import assess_time_offset

__all__ = [
    "ContractValidationResult",
    "ValidationIssue",
    "ValidationReport",
    "assess_examination",
    "assess_time_offset",
    "parse_contract",
    "parse_contract_json",
    "validate_contract",
    "validate_contract_json",
]


def __getattr__(name: str) -> object:
    if name == "assess_time_offset":
        from .time import assess_time_offset

        return assess_time_offset
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
