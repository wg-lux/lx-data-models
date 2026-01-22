from typing import Any, List, cast

import pandas as pd
from pandera.api.pandas.model import DataFrameModel
from pandera.typing import DataFrame

from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.stats.dataset import (
    InterfaceExportDataset,
    KnowledgeBaseDataset,
    LedgerDataset,
)
from lx_dtypes.stats.schemas.knowledge_base import (
    CitationDfSchema,
    ClassificationChoiceDescriptorDfSchema,
    ClassificationChoiceDfSchema,
    ClassificationDfSchema,
    ClassificationTypeDfSchema,
    ExaminationDfSchema,
    ExaminationTypeDfSchema,
    FindingDfSchema,
    FindingTypeDfSchema,
    IndicationDfSchema,
    IndicationTypeDfSchema,
    InformationSourceDfSchema,
    InformationSourceTypeDfSchema,
    InterventionDfSchema,
    InterventionTypeDfSchema,
    UnitDfSchema,
    UnitTypeDfSchema,
)
from lx_dtypes.stats.schemas.ledger import (
    CenterDfSchema,
    ExaminerDfSchema,
    PatientDfSchema,
    PExaminationDfSchema,
    PFindingClassificationChoiceDescriptorDfSchema,
    PFindingClassificationChoiceDfSchema,
    PFindingClassificationsDfSchema,
    PFindingDfSchema,
    PFindingInterventionDfSchema,
    PFindingInterventionsDfSchema,
    PIndicationDfSchema,
)


def _validate_or_empty(schema: type[DataFrameModel], records: List[Any]) -> DataFrame:  # type: ignore # TODO mypy pandera typing issue
    """Validate records against schema; return empty typed frame when none."""

    schema_obj = schema.to_schema()
    if not records:
        dtype = getattr(schema_obj, "dtype", None)
        model_fields = getattr(getattr(dtype, "type", None), "model_fields", {})
        columns = list(model_fields.keys()) or list(schema_obj.columns.keys())
        empty_df = pd.DataFrame(columns=columns)
        validated_df = schema_obj.validate(empty_df)
    else:
        df = pd.DataFrame.from_records(records)
        validated_df = schema_obj.validate(df)

    validated_df = cast(DataFrame, validated_df)  # type: ignore # TODO mypy pandera typing issue

    return validated_df


def kb2dataset(kb: KnowledgeBase) -> KnowledgeBaseDataset:
    record_list = kb.export_record_lists()
    citations = _validate_or_empty(CitationDfSchema, record_list["citations"])
    classifications = _validate_or_empty(
        ClassificationDfSchema, record_list["classifications"]
    )
    classification_types = _validate_or_empty(
        ClassificationTypeDfSchema, record_list["classification_types"]
    )
    classification_choices = _validate_or_empty(
        ClassificationChoiceDfSchema, record_list["classification_choices"]
    )
    classification_choice_descriptors = _validate_or_empty(
        ClassificationChoiceDescriptorDfSchema,
        record_list["classification_choice_descriptors"],
    )
    examinations = _validate_or_empty(ExaminationDfSchema, record_list["examinations"])
    examination_types = _validate_or_empty(
        ExaminationTypeDfSchema, record_list["examination_types"]
    )
    findings = _validate_or_empty(FindingDfSchema, record_list["findings"])
    finding_types = _validate_or_empty(
        FindingTypeDfSchema, record_list["finding_types"]
    )
    indications = _validate_or_empty(IndicationDfSchema, record_list["indications"])
    indication_types = _validate_or_empty(
        IndicationTypeDfSchema, record_list["indication_types"]
    )
    information_sources = _validate_or_empty(
        InformationSourceDfSchema, record_list["information_sources"]
    )
    information_source_types = _validate_or_empty(
        InformationSourceTypeDfSchema, record_list["information_source_types"]
    )
    interventions = _validate_or_empty(
        InterventionDfSchema, record_list["interventions"]
    )
    intervention_types = _validate_or_empty(
        InterventionTypeDfSchema, record_list["intervention_types"]
    )
    units = _validate_or_empty(UnitDfSchema, record_list["units"])
    unit_types = _validate_or_empty(UnitTypeDfSchema, record_list["unit_types"])

    dataset = KnowledgeBaseDataset(
        citations=citations,
        classifications=classifications,
        classification_types=classification_types,
        classification_choices=classification_choices,
        classification_choice_descriptors=classification_choice_descriptors,
        examinations=examinations,
        examination_types=examination_types,
        findings=findings,
        finding_types=finding_types,
        indications=indications,
        indication_types=indication_types,
        information_sources=information_sources,
        information_source_types=information_source_types,
        interventions=interventions,
        intervention_types=intervention_types,
        units=units,
        unit_types=unit_types,
    )
    return dataset


def ledger2dataset(ledger: Ledger) -> LedgerDataset:
    # Implementation would be similar to kb2dataset, tailored for Ledger
    record_lists = ledger.export_record_lists()

    centers = _validate_or_empty(CenterDfSchema, record_lists["centers"])
    examiners = _validate_or_empty(ExaminerDfSchema, record_lists["examiners"])
    patients = _validate_or_empty(PatientDfSchema, record_lists["patients"])
    p_examinations = _validate_or_empty(
        PExaminationDfSchema, record_lists["p_examinations"]
    )
    p_findings = _validate_or_empty(PFindingDfSchema, record_lists["p_findings"])
    p_indications = _validate_or_empty(
        PIndicationDfSchema, record_lists["p_indications"]
    )
    p_finding_classifications = _validate_or_empty(
        PFindingClassificationsDfSchema, record_lists["p_finding_classifications"]
    )
    p_finding_classification_choices = _validate_or_empty(
        PFindingClassificationChoiceDfSchema,
        record_lists["p_finding_classification_choices"],
    )
    p_finding_classification_choice_descriptors = _validate_or_empty(
        PFindingClassificationChoiceDescriptorDfSchema,
        record_lists["p_finding_classification_choice_descriptors"],
    )
    p_finding_interventions = _validate_or_empty(
        PFindingInterventionsDfSchema, record_lists["p_finding_interventions"]
    )
    p_finding_intervention = _validate_or_empty(
        PFindingInterventionDfSchema, record_lists["p_finding_intervention"]
    )

    dataset = LedgerDataset(
        centers=centers,
        examiners=examiners,
        patients=patients,
        p_examinations=p_examinations,
        p_findings=p_findings,
        p_indications=p_indications,
        p_finding_classifications=p_finding_classifications,
        p_finding_classification_choices=p_finding_classification_choices,
        p_finding_classification_choice_descriptors=p_finding_classification_choice_descriptors,
        p_finding_interventions=p_finding_interventions,
        p_finding_intervention=p_finding_intervention,
    )
    return dataset


def interface2dataset(
    patient_interface: DbInterface,
) -> InterfaceExportDataset:
    ledger_dataset = ledger2dataset(ledger=patient_interface.ledger)
    kb_dataset = kb2dataset(kb=patient_interface.knowledge_base)

    dataset = InterfaceExportDataset(
        knowledge_base=kb_dataset,
        ledger=ledger_dataset,
    )
    return dataset
