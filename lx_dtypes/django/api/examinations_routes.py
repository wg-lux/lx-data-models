from __future__ import annotations

from typing import Any, Callable, Dict, List, NoReturn, Protocol, TypeVar

from .findings_routes import (
    _findings_module_name,
    _resolve_exam_kb_finding_names,
    _resolve_kb_finding_classification_names,
    _serialize_finding,
    _norm_name,
)
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...


def _serialize_examination(examination: Any, *, module_name: str) -> Dict[str, Any]:
    findings = list(examination.get_available_findings())
    kb_allowed_finding_names = _resolve_exam_kb_finding_names(
        examination, module_name=module_name
    )
    if kb_allowed_finding_names is not None:
        findings = [
            finding
            for finding in findings
            if _norm_name(finding.name) in kb_allowed_finding_names
        ]

    examination_types_relation = getattr(examination, "examination_types", None)
    examination_types_items = (
        examination_types_relation.all()
        if examination_types_relation is not None
        and hasattr(examination_types_relation, "all")
        else examination_types_relation or []
    )

    return {
        "id": examination.id,
        "name": examination.name,
        "findings": [
            _serialize_finding(
                finding,
                allowed_classification_names=_resolve_kb_finding_classification_names(
                    finding, module_name=module_name
                ),
                required_classification_names=set(),
            )
            for finding in findings
        ],
        "examination_types": [
            {"id": getattr(examination_type, "id", None), "name": examination_type.name}
            for examination_type in examination_types_items
        ],
    }


def register_examinations_routes(
    api: _TypedApi,
    *,
    orm_models: Callable[[], Dict[str, Any]],
    api_error: Callable[[int, str, str], NoReturn],
) -> None:
    @api.get("/examinations/")
    def examinations_catalog(request: BaseRequest) -> List[Dict[str, Any]]:
        del request
        module_name = _findings_module_name()
        examination_model = orm_models()["Examination"]
        examinations = examination_model.objects.all().order_by("id")
        return [
            _serialize_examination(examination, module_name=module_name)
            for examination in examinations
        ]

    @api.get("/examinations/{examination_id}/")
    def examination_detail(request: BaseRequest, examination_id: int) -> Dict[str, Any]:
        del request
        module_name = _findings_module_name()
        examination_model = orm_models()["Examination"]
        examination = examination_model.objects.filter(id=examination_id).first()
        if not examination:
            api_error(404, "not-found", f"Examination '{examination_id}' not found.")
        assert examination is not None
        return _serialize_examination(examination, module_name=module_name)
