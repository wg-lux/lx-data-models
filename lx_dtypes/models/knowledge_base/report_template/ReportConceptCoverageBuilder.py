from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, cast

from .ReportConceptCoverage import (
    REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION,
    ReportConceptApplicability,
    ReportConceptCoverage,
    ReportConceptCoverageIdentity,
    ReportConceptCoverageItem,
    ReportConceptCoverageProvenance,
)
from .ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
    ReportTemplateCoverageFindingSelector,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class _KnowledgeBaseConfig(Protocol):
    def model_dump(self, *, mode: str) -> Mapping[str, Any]: ...


class _CoverageKnowledgeBase(Protocol):
    @property
    def config(self) -> _KnowledgeBaseConfig: ...

    def model_dump(self, *, mode: str) -> Mapping[str, Any]: ...


RESOLVER_NAME = "lx_dtypes.report_concept_coverage"
RESOLVER_VERSION = "1.0.0"
_VOLATILE_KEYS = frozenset({"created_at", "updated_at", "uuid", "tags"})


def _without_volatile_metadata(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _without_volatile_metadata(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if key not in _VOLATILE_KEYS
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_without_volatile_metadata(item) for item in value]
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(
        _without_volatile_metadata(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Report concept coverage requires an explicit non-empty {field}; "
            "lexical names are not accepted as clinical identifiers."
        )
    return value


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(  # noqa: TRY004 - malformed contract value
            f"Report concept coverage expected {field} to be an object."
        )
    return cast(Mapping[str, Any], value)


def _path_exists(payload: Any, path: Sequence[str]) -> bool:
    current = payload
    for segment in path:
        if isinstance(current, Mapping):
            if segment not in current:
                return False
            current = current[segment]
            continue
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                current = current[int(segment)]
            except (IndexError, TypeError, ValueError):
                return False
            continue
        return False
    return True


def _path_value(payload: Any, path: Sequence[str]) -> tuple[bool, Any]:
    current = payload
    for segment in path:
        if isinstance(current, Mapping):
            if segment not in current:
                return False, None
            current = current[segment]
            continue
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            try:
                current = current[int(segment)]
            except (IndexError, TypeError, ValueError):
                return False, None
            continue
        return False, None
    return True, current


def _strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _strict_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    result = left == right
    return result if isinstance(result, bool) else False


def _value_matches_allowed(value: Any, allowed_values: Sequence[Any]) -> bool | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return False
        return all(
            any(_strict_equal(item, allowed) for allowed in allowed_values)
            for item in value
        )
    if isinstance(value, (Mapping, tuple, set)):
        return None
    return any(_strict_equal(value, allowed) for allowed in allowed_values)


def _value_matches_constraint(
    value: Any,
    concept: ReportTemplateCoverageConcept,
) -> bool | None:
    if concept.value_constraint == "non_empty_string":
        return isinstance(value, str) and bool(value.strip())
    if concept.value_constraint == "non_empty_string_list":
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )
    if concept.value_constraint == "number_range":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value):
            return False
        return bool(
            concept.numeric_min is not None
            and concept.numeric_max is not None
            and concept.numeric_min <= value <= concept.numeric_max
        )
    return _value_matches_allowed(value, concept.allowed_values or ())


def _selected_finding_values(
    payload: Mapping[str, Any],
    selector: ReportTemplateCoverageFindingSelector,
    value_path: Sequence[str] | None,
) -> list[tuple[tuple[str, ...], bool, Any]]:
    """Resolve all selector matches in stable payload order.

    ``value_path`` is relative to a selected finding. When a classification is
    selected, the value is the selected classification choice unless an
    explicit relative path is supplied.
    """
    raw_findings = payload.get("patient_findings")
    if not isinstance(raw_findings, Sequence) or isinstance(raw_findings, (str, bytes)):
        return []

    selected: list[tuple[tuple[str, ...], bool, Any]] = []
    for finding_index, raw_finding in enumerate(raw_findings):
        if not isinstance(raw_finding, Mapping):
            continue
        if raw_finding.get("finding") != selector.finding_name:
            continue
        finding_path = ("patient_findings", str(finding_index))
        if not selector.classification_name:
            exists, value = _path_value(raw_finding, value_path or ())
            selected.append((finding_path, exists, value))
            continue

        classifications = raw_finding.get("patient_finding_classifications")
        if not isinstance(classifications, Sequence) or isinstance(
            classifications, (str, bytes)
        ):
            selected.append(
                (finding_path + ("patient_finding_classifications",), False, None)
            )
            continue
        matched_classification = False
        for classification_index, classification in enumerate(classifications):
            if not isinstance(classification, Mapping):
                continue
            choices = classification.get("patient_finding_classification_choices")
            if not isinstance(choices, Sequence) or isinstance(choices, (str, bytes)):
                continue
            for choice_index, choice in enumerate(choices):
                if not isinstance(choice, Mapping):
                    continue
                if choice.get("classification") != selector.classification_name:
                    continue
                if (
                    selector.classification_choice is not None
                    and choice.get("classification_choice")
                    != selector.classification_choice
                ):
                    continue
                matched_classification = True
                choice_path = finding_path + (
                    "patient_finding_classifications",
                    str(classification_index),
                    "patient_finding_classification_choices",
                    str(choice_index),
                )
                if value_path:
                    exists, value = _path_value(choice, value_path)
                else:
                    exists, value = _path_value(choice, ("classification_choice",))
                selected.append((choice_path, exists, value))
        if not matched_classification:
            selected.append(
                (finding_path + ("patient_finding_classifications",), False, None)
            )
    return selected


def _validator_results(validation: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    results: dict[str, Mapping[str, Any]] = {}
    for key in (
        "classification_validators",
        "intervention_validators",
        "findings_validators",
        "examination_validators",
        "unit_validators",
    ):
        raw_results = validation.get(key, ())
        if not isinstance(raw_results, Sequence) or isinstance(
            raw_results, (str, bytes)
        ):
            raise ValueError(  # noqa: TRY004 - malformed contract value
                f"Validator response does not expose {key} as a list."
            )
        for raw_result in raw_results:
            result = _mapping(raw_result, field=f"{key} entries")
            name = _require_text(result.get("name"), field=f"{key} validator name")
            if name in results:
                raise ValueError(
                    f"Validator response contains duplicate validator '{name}'."
                )
            results[name] = result
    return results


def _coerce_coverage_concepts(
    template_export: Mapping[str, Any],
) -> tuple[ReportTemplateCoverageConcept, ...]:
    raw_version = _require_text(
        template_export.get("coverage_version"), field="coverage_version"
    )
    if raw_version != REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION:
        raise ValueError(
            "Report template coverage_version does not match the runtime coverage contract."
        )
    raw_concepts = template_export.get("coverage_concepts")
    if not isinstance(raw_concepts, Sequence) or isinstance(raw_concepts, (str, bytes)):
        raise ValueError(  # noqa: TRY004 - malformed contract value
            "Report template export lacks explicit coverage_concepts; stable concept IDs "
            "and applicability rules must be authored in the template."
        )
    if not raw_concepts:
        raise ValueError("Report template coverage_concepts must not be empty.")
    return tuple(
        ReportTemplateCoverageConcept.model_validate(raw_concept)
        for raw_concept in raw_concepts
    )


def build_report_concept_coverage(
    *,
    kb: _CoverageKnowledgeBase,
    requested_template_name: str,
    template_export: Mapping[str, Any],
    p_examination: PExamination,
    validation: Mapping[str, Any],
) -> ReportConceptCoverage:
    """Build deterministic coverage from one loaded KB and validated PExamination."""
    config = _mapping(kb.config.model_dump(mode="json"), field="KB config")
    module_name = _require_text(config.get("name"), field="module name")
    module_version = _require_text(config.get("version"), field="module version")
    template_name = _require_text(template_export.get("name"), field="template name")
    if template_name != _require_text(
        requested_template_name, field="requested template name"
    ):
        raise ValueError(
            "Report template export identity does not match the requested template."
        )
    template_version = _require_text(
        template_export.get("version"), field="template version"
    )
    concepts = _coerce_coverage_concepts(template_export)
    payload = cast(Mapping[str, Any], p_examination.model_dump(mode="json"))
    validators = _validator_results(validation)
    coverage_items: list[ReportConceptCoverageItem] = []

    for concept in concepts:
        evidence_paths: tuple[tuple[str, ...], ...] = (tuple(concept.evidence_path),)
        if concept.applicability_status == "not_applicable":
            validation_status = "undetermined"
        else:
            validator_states = [
                validators.get(name) for name in concept.validator_names
            ]
            if any(result is None for result in validator_states):
                validation_status = "unknown"
            elif concept.finding_selector is not None:
                selected_values = _selected_finding_values(
                    payload,
                    concept.finding_selector,
                    concept.concept_value_path,
                )
                evidence_paths = tuple(path for path, _, _ in selected_values)
                if not selected_values:
                    validation_status = "missing"
                elif any(
                    not exists or value is None for _, exists, value in selected_values
                ):
                    validation_status = "unknown"
                else:
                    matches = [
                        _value_matches_constraint(value, concept)
                        for _, _, value in selected_values
                    ]
                    if any(match is None for match in matches):
                        validation_status = "unknown"
                    elif any(match is False for match in matches):
                        validation_status = "invalid"
                    else:
                        validation_status = "present"
            elif not _path_exists(payload, concept.evidence_path):
                validation_status = "missing"
            elif any(
                result.get("ok") is False
                for result in validator_states
                if result is not None
            ):
                validation_status = "invalid"
            else:
                value_exists, value = _path_value(
                    payload, concept.concept_value_path or ()
                )
                if not value_exists or value is None:
                    validation_status = "unknown"
                else:
                    value_matches = _value_matches_constraint(value, concept)
                    if value_matches is None:
                        validation_status = "unknown"
                    elif value_matches:
                        validation_status = "present"
                    else:
                        validation_status = "invalid"

        coverage_items.append(
            ReportConceptCoverageItem(
                concept_id=concept.concept_id,
                label=concept.label,
                applicability=ReportConceptApplicability(
                    status=concept.applicability_status,
                    rule=concept.applicability_rule,
                    reason=concept.applicability_reason,
                ),
                validation_status=cast(Any, validation_status),
                evidence_path=evidence_paths[0]
                if evidence_paths
                else tuple(concept.evidence_path),
                evidence_paths=evidence_paths,
                guideline_citations=tuple(concept.guideline_citations),
            )
        )

    return ReportConceptCoverage(
        identity=ReportConceptCoverageIdentity(
            module_name=module_name,
            module_version=module_version,
            module_digest=_digest(kb.model_dump(mode="json")),
            template_name=template_name,
            template_version=template_version,
            template_digest=_digest(template_export),
        ),
        provenance=ReportConceptCoverageProvenance(
            resolver=RESOLVER_NAME,
            resolver_version=RESOLVER_VERSION,
            evidence_digest=_digest({"payload": payload, "validation": validation}),
        ),
        concepts=tuple(coverage_items),
    )


__all__ = ["build_report_concept_coverage"]
