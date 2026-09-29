"""Non-blocking validation at contract, terminology, and study boundaries.

Expected validation failures become reports. Programming errors and broken
knowledge-base configuration still propagate; no persistence is performed.
"""

from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING, Literal

import yaml
from pydantic import BaseModel, TypeAdapter, ValidationError

from lx_dtypes.models.contracts.validation import (
    ContractValidationResult,
    ValidationIssue,
    ValidationReport,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


@lru_cache(maxsize=1)
def _messages() -> dict[str, str]:
    text = files("lx_dtypes").joinpath("validation_messages.yml").read_text("utf-8")
    return TypeAdapter(dict[str, str]).validate_python(
        yaml.safe_load(text), strict=True
    )


def _issue(
    code: str,
    *,
    source: Literal["contract", "terminology", "study"] = "terminology",
    path: tuple[str | int, ...] = (),
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=_messages().get(code, _messages()["contract.invalid"]),
        source=source,
        path=path,
    )


def validate_contract[T: BaseModel](
    model: type[T], payload: object
) -> ContractValidationResult[T]:
    """Collect schema errors without echoing submitted values or exception context.

    Parsing follows the owning model's strictness and validators. Pass Python
    data; JSON text must be decoded by the transport boundary first.
    """
    try:
        # Revalidate model instances too, including mutable ledger models.
        value = model.model_validate(
            payload.model_dump(mode="python")
            if isinstance(payload, BaseModel)
            else payload
        )
    except ValidationError as error:
        return ContractValidationResult[T](
            value=None,
            report=ValidationReport(
                issues=tuple(
                    _issue(
                        f"contract.{item['type']}",
                        source="contract",
                        path=item["loc"],
                    )
                    for item in error.errors(
                        include_input=False, include_context=False, include_url=False
                    )
                )
            ),
        )
    return ContractValidationResult[T](value=value, report=ValidationReport())


def assess_examination(
    knowledge_base: "KnowledgeBase",
    payload: object,
    *,
    template_name: str | None = None,
) -> ValidationReport:
    """Assess ledger data against its pinned terminology and optional study rules.

    Incomplete identity is a warning for legacy ledger records. A conflicting
    identity or semantic failure prevents study evaluation, not draft capture.
    Semantic admissibility reports the first failure from the existing strict
    engine; study evaluation returns all issues collected by that engine.
    """
    from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

    identity = knowledge_base.config.knowledge_base_identity
    parsed = validate_contract(PExamination, payload)
    if parsed.value is None:
        return ValidationReport(
            issues=parsed.report.issues, knowledge_base_identity=identity
        )
    examination = parsed.value
    issues: list[ValidationIssue] = []
    supplied = (examination.knowledge_base_module, examination.knowledge_base_version)
    expected = (identity.knowledge_base_module, identity.knowledge_base_version)
    # A known conflicting component remains an error even if the other is absent.
    if any(
        actual is not None and actual != target
        for actual, target in zip(supplied, expected)
    ):
        issues.append(_issue("terminology.identity_mismatch"))
    elif None in supplied:
        issues.append(
            _issue("terminology.identity_missing").model_copy(
                update={"level": "warning"}
            )
        )
    if (
        template_name is not None
        and template_name not in knowledge_base.report_template
    ):
        issues.append(_issue("terminology.template_unknown"))
    if any(issue.level == "error" for issue in issues):
        return ValidationReport(issues=tuple(issues), knowledge_base_identity=identity)
    try:
        if template_name is None:
            knowledge_base.assert_examination_admissibility(examination)
        else:
            runtime = knowledge_base.evaluate_report_template_validators(
                template_name, p_examination=examination
            )
            issues.extend(
                ValidationIssue(
                    code=item["code"],
                    message=item["message"],
                    level=item["level"],
                    source="study",
                    validator_name=item["validator_name"],
                )
                for item in runtime["issues"]
            )
    except SemanticAdmissibilityError:
        issues.append(_issue("terminology.inadmissible"))
        return ValidationReport(issues=tuple(issues), knowledge_base_identity=identity)
    return ValidationReport(
        issues=tuple(issues),
        knowledge_base_identity=identity,
        study_evaluated=template_name is not None,
    )


__all__ = [
    "ContractValidationResult",
    "ValidationIssue",
    "ValidationReport",
    "assess_examination",
    "validate_contract",
]
