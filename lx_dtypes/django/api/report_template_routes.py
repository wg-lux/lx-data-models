from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Protocol, TypeVar, cast

from ninja.errors import HttpError

from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

from . import report_template_builder
from .report_template_builder import (
    PublishReportTemplateResponse,
    SaveReportTemplateRequest,
    SaveReportTemplateResponse,
    save_report_template_definition,
    set_saved_report_template_lifecycle,
)
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...

    def post(self, path: str, /) -> _RouteDecorator: ...


def _compile_report_template(
    kb: Any,
    template_name: str,
    *,
    mode: Literal["preview", "publish", "production"],
) -> Dict[str, Any]:
    validator = ReportTemplateValidator(kb=kb, compiler=ReportTemplateCompiler(kb=kb))
    return cast(Dict[str, Any], validator.validate_and_compile(template_name, mode=mode))


def _load_builder_module_kb(module_name: str) -> Any:
    loader = DataLoader(input_dirs=[report_template_builder.MODULES_ROOT])
    loader.load_module_configs()
    return loader.load_knowledge_base(module_name)


def register_report_template_routes(
    api: _TypedApi,
    *,
    load_module_kb: Callable[..., Any],
    clear_kb_caches: Callable[[], None],
    resolve_payload_kb_identity: Callable[[str, PExamination], tuple[str, str | None]],
    orm_models: Callable[[], Dict[str, Any]],
    build_p_examination_payload_from_host_ledger: Callable[..., PExamination],
) -> None:
    @api.post("/report-templates/builder/templates")
    def save_report_template(
        request: BaseRequest,
        payload: SaveReportTemplateRequest,
    ) -> SaveReportTemplateResponse:
        """
        Persist a new report-template YAML file into one lx_dtypes knowledge-base module.
        """
        del request
        try:
            saved = save_report_template_definition(payload)
        except FileExistsError as exc:
            raise HttpError(409, str(exc)) from exc
        except ValueError as exc:
            raise HttpError(400, str(exc)) from exc

        clear_kb_caches()
        kb = _load_builder_module_kb(saved.module_name)
        compiled = _compile_report_template(
            kb, saved.template_name, mode="preview"
        )
        saved.readiness = compiled["summary"].model_dump(mode="json")
        return saved

    @api.get("/report-templates/{module_name}/{template_name}")
    def report_template_by_name(
        request: BaseRequest, module_name: str, template_name: str
    ) -> Dict[str, Any]:
        """
        Return a resolved report template JSON payload by module/template name.
        """
        del request
        kb = load_module_kb(module_name)
        try:
            return cast(Dict[str, Any], kb.export_report_template(template_name))
        except KeyError as exc:
            raise HttpError(
                404,
                f"Published report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.get("/report-templates/by-examination/{module_name}/{examination_name}")
    def report_templates_by_examination(
        request: BaseRequest, module_name: str, examination_name: str
    ) -> List[Dict[str, Any]]:
        """
        Return all resolved report templates for the given examination in one module.
        """
        del request
        kb = load_module_kb(module_name)
        matches: list[Dict[str, Any]] = []
        for template_name, template in kb.report_template.items():
            if template.examination != examination_name:
                continue
            if kb.get_report_template_lifecycle_status(template_name) != "published":
                continue
            compiled = _compile_report_template(kb, template_name, mode="production")
            if not compiled["summary"].can_publish:
                continue
            matches.append(kb.export_report_template(template_name))
        return matches

    @api.get("/report-templates/{module_name}/{template_name}/preview")
    def preview_report_template_by_name(
        request: BaseRequest, module_name: str, template_name: str
    ) -> Dict[str, Any]:
        del request
        kb = load_module_kb(module_name)
        try:
            return cast(
                Dict[str, Any], kb.export_report_template_preview(template_name)
            )
        except KeyError as exc:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.post(
        "/report-templates/builder/templates/{module_name}/{template_name}/publish"
    )
    def publish_report_template(
        request: BaseRequest, module_name: str, template_name: str
    ) -> PublishReportTemplateResponse:
        del request
        kb = _load_builder_module_kb(module_name)
        try:
            compiled = _compile_report_template(kb, template_name, mode="publish")
        except KeyError as exc:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

        summary = compiled["summary"]
        if not summary.can_publish:
            raise HttpError(
                409,
                f"Report template '{template_name}' cannot be published until blocking issues are resolved.",
            )

        response = set_saved_report_template_lifecycle(
            module_name=module_name,
            template_name=template_name,
            lifecycle_status="published",
        )
        clear_kb_caches()
        refreshed_kb = _load_builder_module_kb(module_name)
        refreshed = _compile_report_template(
            refreshed_kb, template_name, mode="production"
        )
        response.readiness = refreshed["summary"].model_dump(mode="json")
        return response

    @api.post(
        "/report-templates/builder/templates/{module_name}/{template_name}/unpublish"
    )
    def unpublish_report_template(
        request: BaseRequest, module_name: str, template_name: str
    ) -> PublishReportTemplateResponse:
        del request
        kb = _load_builder_module_kb(module_name)
        if template_name not in kb.report_template:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            )

        response = set_saved_report_template_lifecycle(
            module_name=module_name,
            template_name=template_name,
            lifecycle_status="draft",
        )
        clear_kb_caches()
        refreshed_kb = _load_builder_module_kb(module_name)
        refreshed = _compile_report_template(
            refreshed_kb, template_name, mode="preview"
        )
        response.readiness = refreshed["summary"].model_dump(mode="json")
        return response

    @api.post("/report-templates/{module_name}/{template_name}/validate")
    def validate_report_template_runtime(
        request: BaseRequest,
        module_name: str,
        template_name: str,
        payload: PExamination,
    ) -> Dict[str, Any]:
        """
        Execute report-template validator logic against typed patient examination state.
        """
        del request
        resolved_module_name, resolved_version = resolve_payload_kb_identity(
            module_name, payload
        )
        kb = load_module_kb(resolved_module_name, version=resolved_version)
        try:
            kb.export_report_template(template_name)
            return cast(
                Dict[str, Any],
                kb.evaluate_report_template_validators(
                    template_name, p_examination=payload
                ),
            )
        except SemanticAdmissibilityError as exc:
            raise HttpError(422, str(exc)) from exc
        except KeyError as exc:
            raise HttpError(
                404,
                f"Published report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.post(
        "/report-templates/{module_name}/{template_name}/validate-from-ledger/{patient_examination_id}"
    )
    def validate_report_template_runtime_from_ledger(
        request: BaseRequest,
        module_name: str,
        template_name: str,
        patient_examination_id: int,
    ) -> Dict[str, Any]:
        del request
        patient_examination_model = orm_models()["PatientExamination"]
        patient_examination = patient_examination_model.objects.filter(
            id=patient_examination_id
        ).first()
        if not patient_examination:
            raise HttpError(
                404,
                f"PatientExamination '{patient_examination_id}' not found.",
            )

        try:
            payload = build_p_examination_payload_from_host_ledger(
                patient_examination, route_module_name=module_name
            )
        except ValueError as exc:
            raise HttpError(422, str(exc)) from exc

        resolved_module_name, resolved_version = resolve_payload_kb_identity(
            module_name, payload
        )
        kb = load_module_kb(resolved_module_name, version=resolved_version)
        try:
            kb.export_report_template(template_name)
            return cast(
                Dict[str, Any],
                kb.evaluate_report_template_validators(
                    template_name, p_examination=payload
                ),
            )
        except SemanticAdmissibilityError as exc:
            raise HttpError(422, str(exc)) from exc
        except KeyError as exc:
            raise HttpError(
                404,
                f"Published report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.get("/report-templates/{module_name}/{template_name}/validate-definition")
    def validate_report_template_definition(
        request: BaseRequest, module_name: str, template_name: str
    ) -> Dict[str, Any]:
        del request
        kb = _load_builder_module_kb(module_name)
        try:
            compiled = _compile_report_template(kb, template_name, mode="preview")
        except KeyError as exc:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            ) from exc
        return cast(Dict[str, Any], compiled["summary"].model_dump(mode="json"))

    @api.post("/validators/{module_name}/{validator_kind}/{validator_name}/validate")
    def validate_single_validator_runtime(
        request: BaseRequest,
        module_name: str,
        validator_kind: str,
        validator_name: str,
        payload: PExamination,
    ) -> Dict[str, Any]:
        del request
        resolved_module_name, resolved_version = resolve_payload_kb_identity(
            module_name, payload
        )
        kb = load_module_kb(resolved_module_name, version=resolved_version)

        if validator_kind == "findings_validator":
            if validator_name not in kb.findings_validator:
                raise HttpError(404, f"Unknown findings validator '{validator_name}'.")
            try:
                return cast(
                    Dict[str, Any],
                    kb.evaluate_findings_validator(
                        validator_name, p_examination=payload
                    ),
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "classification_validator":
            if validator_name not in kb.classification_validator:
                raise HttpError(
                    404, f"Unknown classification validator '{validator_name}'."
                )
            try:
                return cast(
                    Dict[str, Any],
                    kb.evaluate_classification_validator(
                        validator_name,
                        p_examination=payload,
                    ),
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "intervention_validator":
            if validator_name not in kb.intervention_validator:
                raise HttpError(
                    404, f"Unknown intervention validator '{validator_name}'."
                )
            try:
                return cast(
                    Dict[str, Any],
                    kb.evaluate_intervention_validator(
                        validator_name, p_examination=payload
                    ),
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "unit_validator":
            if validator_name not in kb.unit_validator:
                raise HttpError(404, f"Unknown unit validator '{validator_name}'.")
            try:
                return cast(
                    Dict[str, Any],
                    kb.evaluate_unit_validator(validator_name, p_examination=payload),
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "examination_validator":
            if validator_name not in kb.examination_validator:
                raise HttpError(
                    404, f"Unknown examination validator '{validator_name}'."
                )
            try:
                return cast(
                    Dict[str, Any],
                    kb.evaluate_examination_validator(
                        validator_name,
                        p_examination=payload,
                    ),
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        raise HttpError(404, f"Unknown validator kind '{validator_kind}'.")
