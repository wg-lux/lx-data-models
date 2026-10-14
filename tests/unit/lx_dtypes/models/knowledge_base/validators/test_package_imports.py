from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "legacy_path, canonical_path",
    [
        (
            "lx_dtypes.models.knowledge_base.report_template.ClassificationValidator",
            "lx_dtypes.models.knowledge_base.validators.ClassificationValidator",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ClassificationValidatorDataDict",
            "lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ExaminationValidator",
            "lx_dtypes.models.knowledge_base.validators.ExaminationValidator",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ExaminationValidatorDataDict",
            "lx_dtypes.models.knowledge_base.validators.ExaminationValidatorDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.FindingsValidator",
            "lx_dtypes.models.knowledge_base.validators.FindingsValidator",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict",
            "lx_dtypes.models.knowledge_base.validators.FindingsValidatorDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.InterventionValidator",
            "lx_dtypes.models.knowledge_base.validators.InterventionValidator",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.InterventionValidatorDataDict",
            "lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.UnitValidator",
            "lx_dtypes.models.knowledge_base.validators.UnitValidator",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.UnitValidatorDataDict",
            "lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference",
            "lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict",
            "lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReferenceDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime",
            "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ValidatorRuntimeDataDict",
            "lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.ValueTypes",
            "lx_dtypes.models.knowledge_base.validators.ValueTypes",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.RuntimeIssues",
            "lx_dtypes.models.knowledge_base.validators.RuntimeIssues",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.FindingTerminologyValidation",
            "lx_dtypes.models.knowledge_base.validators.FindingTerminologyValidation",
        ),
        (
            "lx_dtypes.models.knowledge_base.report_template.FhirFindingInterop",
            "lx_dtypes.models.knowledge_base.fhir.findings",
        ),
        (
            "lx_dtypes.models.knowledge_base.fhir",
            "lx_dtypes.models.knowledge_base.fhir.terminology",
        ),
        (
            "lx_dtypes.models.knowledge_base.fhir_yaml",
            "lx_dtypes.models.knowledge_base.fhir.yaml",
        ),
    ],
)
def test_legacy_modules_reexport_canonical_objects(
    legacy_path: str, canonical_path: str
) -> None:
    legacy = import_module(legacy_path)
    canonical = import_module(canonical_path)
    names = getattr(canonical, "__all__", legacy.__all__)
    assert names
    for name in names:
        assert getattr(legacy, name) is getattr(canonical, name), name
