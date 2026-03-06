from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal

from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from pydantic import Field

from lx_dtypes.models.interface.DataLoader import DataLoader

from .request_types import BaseRequest

api = NinjaAPI()


class ReportTemplateValidationRequest(Schema):
    findings: List[Dict[str, Any]] = Field(default_factory=list)


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
