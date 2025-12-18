from pathlib import Path

# from typing import Any
import pandas as pd
from pandera.typing import DataFrame

# from pydantic import field_serializer#
from lx_dtypes.models.base_models.base_model import DatasetBaseModel

from .schemas import (
    CenterShallowSchema,
    # Knowledge Base
    CitationShallowSchema,
    ClassificationChoiceDescriptorShallowSchema,
    ClassificationChoiceShallowSchema,
    ClassificationShallowSchema,
    ClassificationTypeShallowSchema,
    ExaminationShallowSchema,
    ExaminationTypeShallowSchema,
    ExaminerShallowSchema,
    FindingShallowSchema,
    FindingTypeShallowSchema,
    IndicationShallowSchema,
    IndicationTypeShallowSchema,
    InformationSourceShallowSchema,
    InterventionShallowSchema,
    InterventionTypeShallowSchema,
    PatientExaminationShallowSchema,
    PatientFindingClassificationChoiceDescriptorShallowSchema,
    PatientFindingClassificationChoiceShallowSchema,
    PatientFindingClassificationsShallowSchema,
    PatientFindingShallowSchema,
    PatientShallowSchema,
    UnitShallowSchema,
    UnitTypeShallowSchema,
)


class KnowledgeBaseDataset(DatasetBaseModel):
    """
    A dataset class for managing knowledge base dataframes.
    """

    citations: DataFrame[CitationShallowSchema]
    classification_types: DataFrame[ClassificationTypeShallowSchema]
    classifications: DataFrame[ClassificationShallowSchema]
    classification_choices: DataFrame[ClassificationChoiceShallowSchema]
    classification_choice_descriptors: DataFrame[
        ClassificationChoiceDescriptorShallowSchema
    ]
    examination_types: DataFrame[ExaminationTypeShallowSchema]
    examinations: DataFrame[ExaminationShallowSchema]
    finding_types: DataFrame[FindingTypeShallowSchema]
    findings: DataFrame[FindingShallowSchema]
    indication_types: DataFrame[IndicationTypeShallowSchema]
    indications: DataFrame[IndicationShallowSchema]
    information_sources: DataFrame[InformationSourceShallowSchema]
    intervention_types: DataFrame[InterventionTypeShallowSchema]
    interventions: DataFrame[InterventionShallowSchema]
    unit_types: DataFrame[UnitTypeShallowSchema]
    units: DataFrame[UnitShallowSchema]

    def to_csvs(self, directory_path: Path) -> None:
        """
        Export all dataframes in the dataset to CSV files in the specified directory.

        Args:
            directory_path (Path): The path to the directory where CSV files will be saved.
        """
        directory_path.mkdir(exist_ok=True)
        model_fields = self.model_fields_set
        for field_name in model_fields:
            df = getattr(self, field_name, None)
            if not isinstance(df, pd.DataFrame):
                continue
            file_path = directory_path / f"{field_name}.csv"
            df.to_csv(file_path, index=False)


class PatientLedgerDataset(DatasetBaseModel):
    """
    A dataset class for managing patient ledger dataframes.
    """

    patients: DataFrame[PatientShallowSchema]
    examinations: DataFrame[PatientExaminationShallowSchema]
    findings: DataFrame[PatientFindingShallowSchema]
    classifications: DataFrame[PatientFindingClassificationsShallowSchema]
    classification_choices: DataFrame[PatientFindingClassificationChoiceShallowSchema]
    classification_choice_descriptors: DataFrame[
        PatientFindingClassificationChoiceDescriptorShallowSchema
    ]
    centers: DataFrame[CenterShallowSchema]
    examiners: DataFrame[ExaminerShallowSchema]

    def to_csvs(self, directory_path: Path) -> None:
        """
        Export all dataframes in the dataset to CSV files in the specified directory.

        Args:
            directory_path (Path): The path to the directory where CSV files will be saved.
        """
        directory_path.mkdir(exist_ok=True)
        model_fields = self.model_fields_set
        for field_name in model_fields:
            df = getattr(self, field_name, None)
            if not isinstance(df, pd.DataFrame):
                continue
            file_path = directory_path / f"{field_name}.csv"
            df.to_csv(file_path, index=False)


class InterfaceExportDataset(DatasetBaseModel):
    knowledge_base: KnowledgeBaseDataset
    patient_ledger: PatientLedgerDataset

    def to_csvs(self, directory_path: Path) -> None:
        """
        Export all dataframes in the interface export dataset to CSV files in the specified directory.

        Args:
            directory_path (Path): The path to the directory where CSV files will be saved.
        """
        directory_path.mkdir(exist_ok=True)
        kb_directory = directory_path / "knowledge_base"
        ledger_directory = directory_path / "patient_ledger"
        self.knowledge_base.to_csvs(kb_directory)
        self.patient_ledger.to_csvs(ledger_directory)
