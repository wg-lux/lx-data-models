from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

ReportTemplateIssueSeverityLiteral = Literal["info", "warning", "blocking"]
ReportTemplateLifecycleStatusLiteral = Literal["draft", "published"]
ReportTemplateReadinessLiteral = Literal["draft", "publishable", "published"]
ReportTemplateIssueScopeLiteral = Literal[
    "template",
    "section",
    "finding",
    "validator",
    "examination",
    "registry",
]


class ReportTemplateIssueSourceDataDict(TypedDict, total=False):
    file: str
    line: int
    column: int


class ReportTemplateReadinessIssueDataDict(TypedDict):
    code: str
    severity: ReportTemplateIssueSeverityLiteral
    message: str
    scope: ReportTemplateIssueScopeLiteral
    reference: str | None
    can_preview: bool
    blocks_publish: bool
    source: ReportTemplateIssueSourceDataDict | None


class ReportTemplateReadinessSummaryDataDict(TypedDict):
    lifecycle_status: ReportTemplateLifecycleStatusLiteral
    readiness: ReportTemplateReadinessLiteral
    can_preview: bool
    can_publish: bool
    blocking_issues: int
    warning_issues: int
    info_issues: int
    issues: list[ReportTemplateReadinessIssueDataDict]


class ReportTemplateReadinessIssue(BaseModel):
    code: str
    severity: ReportTemplateIssueSeverityLiteral
    message: str
    scope: ReportTemplateIssueScopeLiteral
    reference: str | None = None
    can_preview: bool = True
    blocks_publish: bool = False
    source: ReportTemplateIssueSourceDataDict | None = None


class ReportTemplateReadinessSummary(BaseModel):
    lifecycle_status: ReportTemplateLifecycleStatusLiteral
    readiness: ReportTemplateReadinessLiteral
    can_preview: bool
    can_publish: bool
    blocking_issues: int
    warning_issues: int
    info_issues: int
    issues: list[ReportTemplateReadinessIssue] = Field(default_factory=list)
