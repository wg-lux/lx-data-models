from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Mapping, Protocol, TypeVar, cast

from ninja.errors import HttpError  # type: ignore[import-untyped]

from lx_dtypes.models.contracts import KnowledgeBaseContract
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverageBuilder import (
    build_report_concept_coverage,
)

from .report_template_builder import (
    PublishReportTemplateResponse,
    ReportTemplateModuleLocation,
    SaveReportTemplateRequest,
    SaveReportTemplateResponse,
    save_report_template_definition,
    set_saved_report_template_lifecycle,
)
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])
ReportTemplateCapability = Literal["report_template:read", "report_template:write"]


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
    return validator.validate_and_compile(template_name, mode=mode)


def _attach_resolved_kb_identity(
    validation: Mapping[str, Any],
    *,
    module_name: str,
    version: str | None,
) -> Dict[str, Any]:
    response = dict(validation)
    response["knowledge_base_module"] = module_name
    response["knowledge_base_version"] = version
    return response


def register_report_template_routes(
    api: _TypedApi,
    *,
    load_module_kb: Callable[..., KnowledgeBaseContract],
    clear_kb_caches: Callable[[], None],
    resolve_builder_module_location: Callable[[str], ReportTemplateModuleLocation],
    resolve_payload_kb_identity: Callable[[str, PExamination], tuple[str, str | None]],
    orm_models: Callable[[], Dict[str, Any]],
    build_p_examination_payload_from_host_ledger: Callable[..., PExamination],
    persist_patient_examination_dtypes_record: Callable[
        [object, PExamination], dict[str, Any]
    ]
    | None = None,
    authenticate_request_user: Callable[[BaseRequest], Any | None],
    report_template_access_allowed: Callable[[object, ReportTemplateCapability], bool],
) -> None:
    def require_builder_access(
        request: BaseRequest, capability: ReportTemplateCapability
    ) -> None:
        actor = authenticate_request_user(request)
        if actor is None:
            raise HttpError(401, "Authentication is required.")
        if not report_template_access_allowed(actor, capability):
            raise HttpError(
                403,
                f"{capability} access is required for report-template builder routes.",
            )

    @api.post("/report-templates/builder/templates")
    def save_report_template(
        request: BaseRequest,
        payload: SaveReportTemplateRequest,
    ) -> SaveReportTemplateResponse:
        """
        Persist a new report-template YAML file into one lx_dtypes knowledge-base module.
        """
        require_builder_access(request, "report_template:write")
        module_name = payload.module_name.strip() or "report_template_examples"
        location = resolve_builder_module_location(module_name)
        try:
            saved = save_report_template_definition(
                payload, modules_root=location.modules_root
            )
        except FileExistsError as exc:
            raise HttpError(409, str(exc)) from exc
        except ValueError as exc:
            raise HttpError(400, str(exc)) from exc

        clear_kb_caches()
        kb = load_module_kb(saved.module_name, version=location.version)
        compiled = _compile_report_template(kb, saved.template_name, mode="preview")
        saved.readiness = compiled["summary"].model_dump(mode="json")
        return saved

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
        for template_name, template in cast(
            Mapping[str, Any], kb.report_template
        ).items():
            template = cast(Any, template)
            if template.examination != examination_name:
                continue
            if kb.get_report_template_lifecycle_status(template_name) != "published":
                continue
            compiled = _compile_report_template(kb, template_name, mode="production")
            if not compiled["summary"].can_publish:
                continue
            matches.append(kb.export_report_template(template_name))
        return matches

    @api.get(
        "/report-templates/builder/by-examination/{module_name}/{examination_name}"
    )
    def builder_report_templates_by_examination(
        request: BaseRequest, module_name: str, examination_name: str
    ) -> List[Dict[str, Any]]:
        """Return preview exports for all builder templates, including drafts."""
        require_builder_access(request, "report_template:read")
        kb = load_module_kb(module_name)
        matches: list[Dict[str, Any]] = []
        for template_name, template in cast(
            Mapping[str, Any], kb.report_template
        ).items():
            template = cast(Any, template)
            if template.examination != examination_name:
                continue
            matches.append(kb.export_report_template_preview(template_name))
        return matches

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
            return kb.export_report_template(template_name)
        except KeyError as exc:
            raise HttpError(
                404,
                f"Published report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.get("/report-templates/{module_name}/{template_name}/preview")
    def preview_report_template_by_name(
        request: BaseRequest, module_name: str, template_name: str
    ) -> Dict[str, Any]:
        require_builder_access(request, "report_template:read")
        kb = load_module_kb(module_name)
        try:
            return kb.export_report_template_preview(template_name)
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
        require_builder_access(request, "report_template:write")
        location = resolve_builder_module_location(module_name)
        kb = load_module_kb(module_name, version=location.version)
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
            modules_root=location.modules_root,
        )
        clear_kb_caches()
        refreshed_kb = load_module_kb(module_name, version=location.version)
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
        require_builder_access(request, "report_template:write")
        location = resolve_builder_module_location(module_name)
        kb = load_module_kb(module_name, version=location.version)
        if template_name not in kb.report_template:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            )

        response = set_saved_report_template_lifecycle(
            module_name=module_name,
            template_name=template_name,
            lifecycle_status="draft",
            modules_root=location.modules_root,
        )
        clear_kb_caches()
        refreshed_kb = load_module_kb(module_name, version=location.version)
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
            template_export = kb.export_report_template(template_name)
            validation = kb.evaluate_report_template_validators(
                template_name, p_examination=payload
            )
            response = _attach_resolved_kb_identity(
                validation,
                module_name=resolved_module_name,
                version=resolved_version,
            )
            response["concept_coverage"] = build_report_concept_coverage(
                kb=cast(Any, kb),
                requested_template_name=template_name,
                template_export=template_export,
                p_examination=payload,
                validation=validation,
            ).model_dump(mode="json")
            return response
        except SemanticAdmissibilityError as exc:
            raise HttpError(422, str(exc)) from exc
        except ValueError as exc:
            raise HttpError(422, str(exc)) from exc
        except KeyError as exc:
            raise HttpError(
                404,
                f"Published report template '{template_name}' not found in module '{module_name}'.",
            ) from exc

    @api.get("/patient-examinations/{patient_examination_id}/dtypes-record/")
    def get_patient_examination_dtypes_record(
        request: BaseRequest,
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
        record = getattr(patient_examination, "dtypes_record", None)
        if not isinstance(record, dict):
            return {}
        return cast(Dict[str, Any], record)

    @api.post("/patient-examinations/{patient_examination_id}/dtypes-record/")
    def persist_patient_examination_dtypes_record_route(
        request: BaseRequest,
        patient_examination_id: int,
        payload: PExamination,
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
        if persist_patient_examination_dtypes_record is None:
            raise HttpError(501, "dtypes record persistence is not configured.")
        try:
            return persist_patient_examination_dtypes_record(
                patient_examination,
                payload,
            )
        except ValueError as exc:
            raise HttpError(422, str(exc)) from exc

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
            template_export = kb.export_report_template(template_name)
            validation = kb.evaluate_report_template_validators(
                template_name, p_examination=payload
            )
            response = _attach_resolved_kb_identity(
                validation,
                module_name=resolved_module_name,
                version=resolved_version,
            )
            response["concept_coverage"] = build_report_concept_coverage(
                kb=cast(Any, kb),
                requested_template_name=template_name,
                template_export=template_export,
                p_examination=payload,
                validation=validation,
            ).model_dump(mode="json")
            return response
        except SemanticAdmissibilityError as exc:
            raise HttpError(422, str(exc)) from exc
        except ValueError as exc:
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
        require_builder_access(request, "report_template:read")
        kb = load_module_kb(module_name)
        if template_name not in kb.report_template:
            raise HttpError(
                404,
                f"Report template '{template_name}' not found in module '{module_name}'.",
            )
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
                validation = kb.evaluate_findings_validator(
                    validator_name, p_examination=payload
                )
                return _attach_resolved_kb_identity(
                    validation,
                    module_name=resolved_module_name,
                    version=resolved_version,
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "classification_validator":
            if validator_name not in kb.classification_validator:
                raise HttpError(
                    404, f"Unknown classification validator '{validator_name}'."
                )
            try:
                validation = kb.evaluate_classification_validator(
                    validator_name,
                    p_examination=payload,
                )
                return _attach_resolved_kb_identity(
                    validation,
                    module_name=resolved_module_name,
                    version=resolved_version,
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "intervention_validator":
            if validator_name not in kb.intervention_validator:
                raise HttpError(
                    404, f"Unknown intervention validator '{validator_name}'."
                )
            try:
                validation = kb.evaluate_intervention_validator(
                    validator_name, p_examination=payload
                )
                return _attach_resolved_kb_identity(
                    validation,
                    module_name=resolved_module_name,
                    version=resolved_version,
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "unit_validator":
            if validator_name not in kb.unit_validator:
                raise HttpError(404, f"Unknown unit validator '{validator_name}'.")
            try:
                validation = kb.evaluate_unit_validator(
                    validator_name, p_examination=payload
                )
                return _attach_resolved_kb_identity(
                    validation,
                    module_name=resolved_module_name,
                    version=resolved_version,
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        if validator_kind == "examination_validator":
            if validator_name not in kb.examination_validator:
                raise HttpError(
                    404, f"Unknown examination validator '{validator_name}'."
                )
            try:
                validation = kb.evaluate_examination_validator(
                    validator_name,
                    p_examination=payload,
                )
                return _attach_resolved_kb_identity(
                    validation,
                    module_name=resolved_module_name,
                    version=resolved_version,
                )
            except SemanticAdmissibilityError as exc:
                raise HttpError(422, str(exc)) from exc

        raise HttpError(404, f"Unknown validator kind '{validator_kind}'.")
