"""Portable label presentation and explicit study whitelist configuration."""

from typing import Self, TypedDict

from pydantic import ConfigDict, Field, model_validator

from lx_dtypes.models.model import StrictContractModel


class StudyLabelAppearance(StrictContractModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class StudyLabelScope(StrictContractModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(min_length=1, max_length=255)
    labels: list[str] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_labels(self) -> Self:
        if len(self.labels) != len(set(self.labels)):
            raise ValueError("scope label references must be unique")
        return self


class StudyLabelPresentation(StrictContractModel):
    """List order controls display; hosts enforce locked whitelists in study scope.

    An empty locked list permits no new label assignments. Scopes are display
    groups, not user roles, and never grant or remove host authorization.
    """

    locked: bool = False
    labels: list[StudyLabelAppearance] = Field(default_factory=list, max_length=1000)
    scopes: list[StudyLabelScope] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_and_resolved_references(self) -> Self:
        names = [label.name for label in self.labels]
        scope_names = [scope.name for scope in self.scopes]
        if len(names) != len(set(names)) or len(scope_names) != len(set(scope_names)):
            raise ValueError("label and scope names must be unique")
        configured = set(names)
        if any(set(scope.labels) - configured for scope in self.scopes):
            raise ValueError("scope labels must reference configured labels")
        return self


class StudyAnnotationLabel(StudyLabelAppearance):
    id: int = Field(gt=0)


class StudyAnnotationLabelCatalog(StrictContractModel):
    study_cohort_id: int | None = Field(default=None, gt=0)
    locked: bool
    labels: list[StudyAnnotationLabel]
    scopes: list[StudyLabelScope]


class StudyLabelAppearanceDataDict(TypedDict):
    name: str
    display_name: str | None
    color: str | None


class StudyLabelScopeDataDict(TypedDict):
    name: str
    display_name: str
    labels: list[str]


class StudyLabelPresentationDataDict(TypedDict):
    locked: bool
    labels: list[StudyLabelAppearanceDataDict]
    scopes: list[StudyLabelScopeDataDict]
