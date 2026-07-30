from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class _KnowledgeBaseConfig(Protocol):
    def model_dump(self, *, mode: str) -> Mapping[str, Any]: ...


class _CoverageKnowledgeBase(Protocol):
    @property
    def config(self) -> _KnowledgeBaseConfig: ...

    def model_dump(self, *, mode: str) -> Mapping[str, Any]: ...

from .ReportConceptCoverage import (
    REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION,
    ReportConceptApplicability,
    ReportConceptCoverage,
    ReportConceptCoverageIdentity,
    ReportConceptCoverageItem,
    ReportConceptCoverageProvenance,
)
from .ReportTemplateCoverage import ReportTemplateCoverageConcept


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
        raise ValueError(f"Report concept coverage expected {field} to be an object.")
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
            raise ValueError(f"Validator response does not expose {key} as a list.")
        for raw_result in raw_results:
            result = _mapping(raw_result, field=f"{key} entries")
            name = _require_text(result.get("name"), field=f"{key} validator name")
            if name in results:
                raise ValueError(f"Validator response contains duplicate validator '{name}'.")
            results[name] = result
    return results


def _coerce_coverage_concepts(template_export: Mapping[str, Any]) -> tuple[ReportTemplateCoverageConcept, ...]:
    raw_version = _require_text(
        template_export.get("coverage_version"), field="coverage_version"
    )
    if raw_version != REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION:
        raise ValueError(
            "Report template coverage_version does not match the runtime coverage contract."
        )
    raw_concepts = template_export.get("coverage_concepts")
    if not isinstance(raw_concepts, Sequence) or isinstance(raw_concepts, (str, bytes)):
        raise ValueError(
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
        if concept.applicability_status == "not_applicable":
            validation_status = "undetermined"
        else:
            validator_states = [validators.get(name) for name in concept.validator_names]
            if any(result is None for result in validator_states):
                validation_status = "unknown"
            elif not _path_exists(payload, concept.evidence_path):
                validation_status = "missing"
            elif any(
                result.get("ok") is False
                for result in validator_states
                if result is not None
            ):
                validation_status = "invalid"
            else:
                validation_status = "present"

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
                evidence_path=tuple(concept.evidence_path),
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
