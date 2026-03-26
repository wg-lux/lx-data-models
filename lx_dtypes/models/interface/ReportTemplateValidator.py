from typing import TYPE_CHECKING, Any, Dict, List, Literal, Self, Tuple, cast

from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph import (
    validate_report_template_structure,
)
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateIssueSourceDataDict,
    ReportTemplateLifecycleStatusLiteral,
    ReportTemplateReadinessIssue,
    ReportTemplateReadinessSummary,
)
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


class ReportTemplateValidator:
    """
    Validates ReportTemplates and compiles a readiness summary based on
    various checks and references within the KnowledgeBase.
    """

    def __init__(self, kb: "KnowledgeBase", compiler: ReportTemplateCompiler):
        self.kb = kb
        self.compiler = compiler

    def _issue_source_for_template_record(
        self,
        *,
        scope: Literal["template", "section", "finding", "validator", "examination"],
        reference: str,
    ) -> ReportTemplateIssueSourceDataDict | None:
        record: Any | None = None
        if scope == "template":
            record = self.kb.report_template.get(reference)
        elif scope == "section":
            record = self.kb.report_template_section.get(reference)
        elif scope == "finding":
            record = self.kb.report_finding.get(reference) or self.kb.finding.get(
                reference
            )
        elif scope == "validator":
            record = (
                self.kb.findings_validator.get(reference)
                or self.kb.examination_validator.get(reference)
                or self.kb.classification_validator.get(reference)
                or self.kb.intervention_validator.get(reference)
                or self.kb.unit_validator.get(reference)
            )
        elif scope == "examination":
            record = self.kb.examination.get(reference)

        source_file = getattr(record, "source_file", None)
        if source_file is None:
            return None
        return {"file": str(source_file)}

    def _make_report_template_issue(
        self,
        *,
        code: str,
        severity: Literal["info", "warning", "blocking"],
        message: str,
        scope: Literal[
            "template", "section", "finding", "validator", "examination", "registry"
        ],
        reference: str | None = None,
        can_preview: bool = True,
        blocks_publish: bool | None = None,
    ) -> ReportTemplateReadinessIssue:
        if blocks_publish is None:
            blocks_publish = severity == "blocking"
        source = None
        if reference and scope in {
            "template",
            "section",
            "finding",
            "validator",
            "examination",
        }:
            source = self._issue_source_for_template_record(
                scope=cast(
                    Literal["template", "section", "finding", "validator", "examination"],
                    scope,
                ),
                reference=reference,
            )
        return ReportTemplateReadinessIssue(
            code=code,
            severity=severity,
            message=message,
            scope=scope,
            reference=reference,
            can_preview=can_preview,
            blocks_publish=blocks_publish,
            source=source,
        )

    def validate_and_compile(
        self, name: str, *, mode: Literal["preview", "publish", "production"] = "preview"
    ) -> Dict[str, Any]:
        template = self.kb.get_report_template(name)
        lifecycle_status = self.kb.get_report_template_lifecycle_status(name)
        issues: List[ReportTemplateReadinessIssue] = []

        if template.examination not in self.kb.examination:
            issues.append(
                self._make_report_template_issue(
                    code="unknown_template_examination",
                    severity="blocking",
                    message=(
                        f"Template '{name}' references unknown examination "
                        f"'{template.examination}'."
                    ),
                    scope="examination",
                    reference=template.examination,
                )
            )

        structure_result = validate_report_template_structure(
            template,
            sections=self.kb.report_template_section,
            report_findings=self.kb.report_finding,
            findings=self.kb.finding,
        )
        blocking_structure_codes = {
            "missing_section",
            "invalid_finding_reference",
            "unknown_finding_reference",
            "invalid_section_field",
        }
        for issue in structure_result.issues:
            reference = None
            scope: Literal[
                "template",
                "section",
                "finding",
                "validator",
                "examination",
                "registry",
            ] = "template"
            node_id = issue.node_id or ""
            if ":" in node_id:
                prefix, _, suffix = node_id.partition(":")
                reference = suffix or None
                if prefix == "section":
                    scope = "section"
                elif prefix == "finding":
                    scope = "finding"
            is_publish_blocking = (
                issue.level == "error" or issue.code in blocking_structure_codes
            )
            issues.append(
                self._make_report_template_issue(
                    code=issue.code,
                    severity="blocking" if is_publish_blocking else "warning",
                    message=issue.message,
                    scope=scope,
                    reference=reference,
                    can_preview=True,
                    blocks_publish=is_publish_blocking,
                )
            )

        validator_checks: List[Tuple[str, str, List[str], Dict[str, Any]]] = [
            (
                "unknown_examination_validator_reference",
                "examination_validator",
                list(template.validators.examination_validators),
                self.kb.examination_validator,
            ),
            (
                "unknown_classification_validator_reference",
                "classification_validator",
                list(template.validators.classification_validators),
                self.kb.classification_validator,
            ),
            (
                "unknown_intervention_validator_reference",
                "intervention_validator",
                list(template.validators.intervention_validators),
                self.kb.intervention_validator,
            ),
            (
                "unknown_unit_validator_reference",
                "unit_validator",
                list(template.validators.unit_validators),
                self.kb.unit_validator,
            ),
            (
                "unknown_findings_validator_reference",
                "findings_validator",
                list(template.validators.findings_validators),
                self.kb.findings_validator,
            ),
        ]
        for code, label, names, registry in validator_checks:
            for validator_name in names:
                registry_dict: Dict[str, Any] = registry
                if validator_name in registry_dict:
                    continue

                issues.append(
                    self._make_report_template_issue(
                        code=code,
                        severity="warning",
                        message=(
                            f"Template '{name}' references missing {label} "
                            f"'{validator_name}'."
                        ),
                        scope="validator",
                        reference=validator_name,
                        can_preview=True,
                        blocks_publish=True,
                    )
                )

        for validator_name, validator in self.kb.findings_validator.items():
            if validator_name not in template.validators.findings_validators:
                continue
            if validator.finding not in self.kb.finding:
                issues.append(
                    self._make_report_template_issue(
                        code="validator_finding_missing_in_knowledge_base",
                        severity="warning",
                        message=(
                            f"Findings validator '{validator_name}' targets unknown finding "
                            f"'{validator.finding}'."
                        ),
                        scope="validator",
                        reference=validator_name,
                        can_preview=True,
                        blocks_publish=True,
                    )
                )

        # Hydrate the template using the compiler
        payload = self.compiler.compile(name)

        blocking_issues = [issue for issue in issues if issue.blocks_publish]
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")
        can_publish = len(blocking_issues) == 0
        can_preview = all(issue.can_preview for issue in issues) if issues else True
        readiness = (
            "published"
            if lifecycle_status == "published" and can_publish
            else "publishable"
            if can_publish
            else "draft"
        )
        summary = ReportTemplateReadinessSummary(
            lifecycle_status=lifecycle_status,
            readiness=cast(
                Literal["draft", "publishable", "published"], readiness
            ),
            can_preview=can_preview,
            can_publish=can_publish,
            blocking_issues=len(blocking_issues),
            warning_issues=warning_count,
            info_issues=info_count,
            issues=issues,
        )

        payload["lifecycle_status"] = lifecycle_status
        payload["readiness"] = summary.model_dump(mode="json")
        payload["issues"] = [issue.model_dump(mode="json") for issue in issues]
        return {
            "template": payload,
            "summary": summary,
        }
