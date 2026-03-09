import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal

from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from pydantic import Field

from lx_dtypes.models.interface.DataLoader import DataLoader

from .request_types import BaseRequest

api = NinjaAPI()
logger = logging.getLogger(__name__)
DEFAULT_REQUIREMENT_MODULE = "report_template_examples"

_ENDOREG_DB_IMPORT_ERROR: Exception | None = None
try:
    from endoreg_db.models import Examination, FindingClassification
    from endoreg_db.utils.translation import build_multilingual_response
except Exception as exc:  # pragma: no cover - optional integration in this module
    _ENDOREG_DB_IMPORT_ERROR = exc
    Examination = None  # type: ignore[assignment]
    FindingClassification = None  # type: ignore[assignment]
    build_multilingual_response = None  # type: ignore[assignment]


class ReportTemplateValidationRequest(Schema):
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class EvaluateRequirementSetRequest(Schema):
    requirement_set_id: int | None = None
    requirement_set_ids: List[int] = Field(default_factory=list)
    requirementSetIds: List[int] = Field(default_factory=list)
    patient_examination_id: int | None = None
    module_name: str | None = None
    reported_findings: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class FrontendErrorLogRequest(Schema):
    message: str
    stack: str | None = None
    url: str | None = None
    user_agent: str | None = None
    timestamp: str | None = None
    error_type: str | None = None
    context: Dict[str, Any] = Field(default_factory=dict)


@lru_cache(maxsize=1)
def _kb_loader() -> DataLoader:
    package_data_dir = Path(__file__).resolve().parents[2] / "data"
    legacy_cwd_data_dir = Path("./lx_dtypes/data/").resolve()
    input_dirs = [
        data_dir
        for data_dir in (package_data_dir, legacy_cwd_data_dir)
        if data_dir.exists()
    ]
    loader = DataLoader(input_dirs=input_dirs or [package_data_dir])
    loader.load_module_configs()
    return loader


def _load_module_kb(module_name: str):
    loader = _kb_loader()
    try:
        return loader.load_knowledge_base(module_name)
    except ValueError as exc:
        raise HttpError(404, f"Unknown knowledge-base module '{module_name}'.") from exc


def _ensure_endoreg_db_available() -> None:
    if _ENDOREG_DB_IMPORT_ERROR is None:
        return
    raise HttpError(
        503,
        f"endoreg_db integration is unavailable for base_api endpoints: {_ENDOREG_DB_IMPORT_ERROR}",
    )


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stable_requirement_sets(
    kb: Any,
    *,
    module_name: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for template_id, template_name in enumerate(sorted(kb.report_template.keys()), start=1):
        template = kb.report_template[template_name]
        requirements: List[Dict[str, Any]] = []
        requirement_id = 1
        for validator_name in template.validators.findings_validators:
            requirements.append(
                {
                    "id": requirement_id,
                    "name": str(validator_name),
                    "description": "Findings validator",
                    "kind": "findings_validator",
                    "met": False,
                }
            )
            requirement_id += 1
        for validator_name in template.validators.examination_validators:
            requirements.append(
                {
                    "id": requirement_id,
                    "name": str(validator_name),
                    "description": "Examination validator",
                    "kind": "examination_validator",
                    "met": False,
                }
            )
            requirement_id += 1

        rows.append(
            {
                "id": template_id,
                "name": template_name,
                "description": f"Report template requirements for '{template_name}'.",
                "type": str(template.examination),
                "module_name": module_name,
                "template_name": template_name,
                "requirements": requirements,
                "met": False,
            }
        )
    return rows


def _collect_requirement_set_ids(
    payload: EvaluateRequirementSetRequest,
) -> tuple[List[int], bool]:
    candidates: List[Any] = []
    if payload.requirement_set_id is not None:
        candidates.append(payload.requirement_set_id)
    candidates.extend(payload.requirement_set_ids or [])
    candidates.extend(payload.requirementSetIds or [])

    ids: List[int] = []
    seen: set[int] = set()
    for candidate in candidates:
        set_id = _to_int(candidate)
        if set_id is None or set_id <= 0 or set_id in seen:
            continue
        seen.add(set_id)
        ids.append(set_id)
    return ids, bool(candidates)


def _validator_details(validator_result: Dict[str, Any]) -> str:
    if bool(validator_result.get("ok")):
        return "Validator passed"

    issues = validator_result.get("issues")
    if isinstance(issues, list):
        issue_messages = [
            str(issue.get("message"))
            for issue in issues
            if isinstance(issue, dict) and issue.get("message")
        ]
        if issue_messages:
            return " | ".join(issue_messages[:3])
    return "Validator failed"


@api.get("/hello")
def hello(request: BaseRequest) -> Literal["Hello world"]:
    """
    Return the fixed greeting used as the /hello endpoint response.

    Returns:
        The exact string "Hello world" returned to clients.
    """
    return "Hello world"


@api.get("/report-templates/{module_name}/{template_name}")
def report_template_by_name(
    request: BaseRequest, module_name: str, template_name: str
) -> Dict[str, Any]:
    """
    Return a resolved report template JSON payload by module/template name.
    """
    kb = _load_module_kb(module_name)
    try:
        return kb.export_report_template(template_name)
    except KeyError as exc:
        raise HttpError(
            404,
            f"Report template '{template_name}' not found in module '{module_name}'.",
        ) from exc


@api.get("/report-templates/by-examination/{module_name}/{examination_name}")
def report_templates_by_examination(
    request: BaseRequest, module_name: str, examination_name: str
) -> List[Dict[str, Any]]:
    """
    Return all resolved report templates for the given examination in one module.
    """
    kb = _load_module_kb(module_name)
    matches = [
        kb.export_report_template(template_name)
        for template_name, template in kb.report_template.items()
        if template.examination == examination_name
    ]
    return matches


@api.post("/report-templates/{module_name}/{template_name}/validate")
def validate_report_template_runtime(
    request: BaseRequest,
    module_name: str,
    template_name: str,
    payload: ReportTemplateValidationRequest,
) -> Dict[str, Any]:
    """
    Execute report-template validator logic against runtime finding payload data.
    """
    kb = _load_module_kb(module_name)
    try:
        return kb.evaluate_report_template_validators(
            template_name, reported_findings=payload.findings
        )
    except KeyError as exc:
        raise HttpError(
            404,
            f"Report template '{template_name}' not found in module '{module_name}'.",
        ) from exc


@api.get("/core-concepts/{module_name}")
def core_concepts_by_module(request: BaseRequest, module_name: str) -> Dict[str, Any]:
    """
    Return canonical core concept payloads for one KB module.
    """
    kb = _load_module_kb(module_name)
    return kb.export_core_concepts()


@api.get("/examinations/{examination_id}/classifications")
def base_api_examination_classifications(
    request: BaseRequest, examination_id: int
) -> List[Dict[str, Any]]:
    """
    Return all finding classifications linked to an examination.
    """
    _ensure_endoreg_db_available()
    if examination_id <= 0:
        raise HttpError(400, "examination_id must be a positive integer.")

    if not Examination.objects.filter(id=examination_id).exists():
        raise HttpError(404, f"Examination with id {examination_id} does not exist.")

    classifications = FindingClassification.objects.filter(examinations__id=examination_id)
    return [build_multilingual_response(c) for c in classifications]


@api.get("/requirement-sets")
def base_api_requirement_sets(
    request: BaseRequest,
    module_name: str = DEFAULT_REQUIREMENT_MODULE,
    examination_name: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Return requirement sets derived from KB report templates and validators.
    """
    kb = _load_module_kb(module_name)
    requirement_sets = _stable_requirement_sets(kb, module_name=module_name)
    if not examination_name:
        return requirement_sets
    return [
        row
        for row in requirement_sets
        if str(row.get("type", "")) == str(examination_name)
    ]


@api.get("/requirement-sets/{requirement_set_id}")
def base_api_requirement_set_detail(
    request: BaseRequest,
    requirement_set_id: int,
    module_name: str = DEFAULT_REQUIREMENT_MODULE,
) -> Dict[str, Any]:
    """
    Return one requirement set derived from a KB report template.
    """
    if requirement_set_id <= 0:
        raise HttpError(400, "requirement_set_id must be a positive integer.")
    kb = _load_module_kb(module_name)
    requirement_sets = _stable_requirement_sets(kb, module_name=module_name)
    for requirement_set in requirement_sets:
        if requirement_set["id"] == requirement_set_id:
            return requirement_set
    raise HttpError(404, f"RequirementSet with id {requirement_set_id} does not exist.")


@api.post("/evaluate-requirement-set")
def base_api_evaluate_requirement_set(
    request: BaseRequest, payload: EvaluateRequirementSetRequest
) -> Dict[str, Any]:
    """
    Evaluate requirement sets against runtime findings via dtypes validators.
    """
    module_name = str(payload.module_name or DEFAULT_REQUIREMENT_MODULE)
    kb = _load_module_kb(module_name)
    requirement_sets = _stable_requirement_sets(kb, module_name=module_name)
    requirement_set_map = {row["id"]: row for row in requirement_sets}

    selected_set_ids, set_ids_provided = _collect_requirement_set_ids(payload)
    if not selected_set_ids:
        if set_ids_provided:
            selected_set_ids = []
        else:
            selected_set_ids = list(requirement_set_map.keys())

    errors: List[str] = []
    if set_ids_provided and not selected_set_ids:
        errors.append(
            "At least one valid positive requirement_set_id must be provided."
        )
    patient_examination_id = _to_int(payload.patient_examination_id)
    reported_findings = payload.reported_findings or payload.findings or []

    results: List[Dict[str, Any]] = []
    seen_set_ids: set[int] = set()
    for set_id in selected_set_ids:
        requirement_set = requirement_set_map.get(set_id)
        if requirement_set is None:
            errors.append(f"No RequirementSets found for IDs: [{set_id}]")
            continue

        template_name = str(requirement_set.get("template_name") or requirement_set["name"])
        try:
            runtime = kb.evaluate_report_template_validators(
                template_name, reported_findings=reported_findings
            )
        except Exception as exc:
            logger.exception(
                "base_api evaluate-requirement-set failed (module=%s, set_id=%s, template=%s)",
                module_name,
                set_id,
                template_name,
            )
            errors.append(
                f"Requirement evaluation failed for set {set_id} ('{template_name}'): {exc}"
            )
            continue

        seen_set_ids.add(set_id)
        findings_results = runtime.get("findings_validators") or []
        examination_results = runtime.get("examination_validators") or []
        for validator_result in [*findings_results, *examination_results]:
            if not isinstance(validator_result, dict):
                continue
            requirement_name = str(validator_result.get("name") or "unknown_validator")
            met = bool(validator_result.get("ok"))
            detail = _validator_details(validator_result)

            results.append(
                {
                    "requirement_set_id": set_id,
                    "requirement_set_name": str(requirement_set["name"]),
                    "requirement_name": requirement_name,
                    "met": met,
                    "details": detail,
                    "validator_result": validator_result,
                    "error": None,
                    "status": "PASSED" if met else "FAILED",
                }
            )

    if errors and results:
        status_label = "partial"
    elif errors:
        status_label = "failed"
    else:
        status_label = "ok"

    return {
        "ok": not errors,
        "errors": errors,
        "meta": {
            "patient_examination_id": patient_examination_id,
            "module_name": module_name,
            "sets_evaluated": len(seen_set_ids),
            "requirements_evaluated": len(results),
            "status": status_label,
        },
        "results": results,
    }


@api.get("/images")
def base_api_images(request: BaseRequest) -> List[Dict[str, Any]]:
    """
    Compatibility endpoint for legacy image queue consumers.
    """
    return []


@api.post("/log-frontend-error")
def base_api_log_frontend_error(
    request: BaseRequest, payload: FrontendErrorLogRequest
) -> Dict[str, Any]:
    """
    Accept and log frontend runtime errors.
    """
    logger.warning(
        "frontend_error type=%s message=%s url=%s",
        payload.error_type or "unknown",
        payload.message,
        payload.url or "",
    )
    if payload.stack:
        logger.debug("frontend_error_stack: %s", payload.stack)
    return {"ok": True}
