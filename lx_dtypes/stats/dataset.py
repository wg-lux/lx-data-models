from pathlib import Path

# from typing import Any
import pandas as pd
from pandera.typing import DataFrame

from .common import DatasetBaseModel
from .schemas.knowledge_base import (
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
from .schemas.ledger import (
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


class LedgerDataset(DatasetBaseModel):
    """
    A dataset class for managing ledger dataframes.
    """

    patients: DataFrame[PatientDfSchema]
    centers: DataFrame[CenterDfSchema]
    examiners: DataFrame[ExaminerDfSchema]
    p_examinations: DataFrame[PExaminationDfSchema]
    p_findings: DataFrame[PFindingDfSchema]
    p_indications: DataFrame[PIndicationDfSchema]
    p_finding_classifications: DataFrame[PFindingClassificationsDfSchema]
    p_finding_classification_choices: DataFrame[PFindingClassificationChoiceDfSchema]
    p_finding_classification_choice_descriptors: DataFrame[
        PFindingClassificationChoiceDescriptorDfSchema
    ]
    p_finding_interventions: DataFrame[PFindingInterventionsDfSchema]
    p_finding_intervention: DataFrame[PFindingInterventionDfSchema]

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

    def to_xlsx(self, file_path: Path) -> None:
        """
        Export all dataframes in the dataset to a single Excel file with multiple sheets.

        Args:
            file_path (Path): The path to the Excel file where data will be saved.
        """

        def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
            tz_cols = df.select_dtypes(include=["datetimetz"]).columns
            if not len(tz_cols):
                return df
            df = df.copy()
            for col in tz_cols:
                df[col] = df[col].dt.tz_convert("UTC").dt.tz_localize(None)  # type: ignore
            return df

        with pd.ExcelWriter(file_path) as writer:
            model_fields = self.model_fields_set
            for field_name in model_fields:
                df = getattr(self, field_name, None)
                if not isinstance(df, pd.DataFrame):
                    continue
                _strip_tz(df).to_excel(writer, sheet_name=field_name, index=False)


class KnowledgeBaseDataset(DatasetBaseModel):
    """
    A dataset class for managing knowledge base dataframes.
    """

    citations: DataFrame[CitationDfSchema]
    classifications: DataFrame[ClassificationDfSchema]
    classification_types: DataFrame[ClassificationTypeDfSchema]
    classification_choices: DataFrame[ClassificationChoiceDfSchema]
    classification_choice_descriptors: DataFrame[ClassificationChoiceDescriptorDfSchema]
    examinations: DataFrame[ExaminationDfSchema]
    examination_types: DataFrame[ExaminationTypeDfSchema]
    findings: DataFrame[FindingDfSchema]
    finding_types: DataFrame[FindingTypeDfSchema]
    indications: DataFrame[IndicationDfSchema]
    indication_types: DataFrame[IndicationTypeDfSchema]
    information_sources: DataFrame[InformationSourceDfSchema]
    information_source_types: DataFrame[InformationSourceTypeDfSchema]
    interventions: DataFrame[InterventionDfSchema]
    intervention_types: DataFrame[InterventionTypeDfSchema]
    units: DataFrame[UnitDfSchema]
    unit_types: DataFrame[UnitTypeDfSchema]

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

    def to_xlsx(self, file_path: Path) -> None:
        """
        Export all dataframes in the dataset to a single Excel file with multiple sheets.

        Args:
            file_path (Path): The path to the Excel file where data will be saved.
        """

        def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
            tz_cols = df.select_dtypes(include=["datetimetz"]).columns
            if not len(tz_cols):
                return df
            df = df.copy()
            for col in tz_cols:
                df[col] = df[col].dt.tz_convert("UTC").dt.tz_localize(None)  # type: ignore
            return df

        with pd.ExcelWriter(file_path) as writer:
            model_fields = self.model_fields_set
            for field_name in model_fields:
                df = getattr(self, field_name, None)
                if not isinstance(df, pd.DataFrame):
                    continue
                _strip_tz(df).to_excel(writer, sheet_name=field_name, index=False)


class InterfaceExportDataset(DatasetBaseModel):
    knowledge_base: KnowledgeBaseDataset
    ledger: LedgerDataset

    def to_csvs(self, directory_path: Path) -> None:
        """
        Export all dataframes in the interface export dataset to CSV files in the specified directory.

        Args:
            directory_path (Path): The path to the directory where CSV files will be saved.
        """
        directory_path.mkdir(exist_ok=True)
        kb_directory = directory_path / "knowledge_base"
        ledger_directory = directory_path / "ledger"
        self.knowledge_base.to_csvs(kb_directory)
        self.ledger.to_csvs(ledger_directory)

    def to_xlsx(self, file_path: Path, overwrite: bool = False) -> None:
        """
        Export all dataframes in the interface export dataset to a single Excel file with multiple sheets.

        Args:
            file_path (Path): The path to the Excel file where data will be saved.
        """
        # abort if file_path.exists():
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File {file_path} already exists. Aborting export.")
        elif file_path.exists() and overwrite:
            file_path.unlink()
        with pd.ExcelWriter(file_path) as writer:
            # Export ledger dataframes
            ledger_model_fields = self.ledger.model_fields_set
            for field_name in ledger_model_fields:
                df = getattr(self.ledger, field_name, None)
                if not isinstance(df, pd.DataFrame):
                    continue
                sheet_name = f"l_{field_name}"[:31]  # Excel sheet name max length is 31
                tz_cols = df.select_dtypes(include=["datetimetz"]).columns
                export_df = df
                if len(tz_cols):
                    export_df = df.copy()
                    for col in tz_cols:
                        export_df[col] = (
                            export_df[col].dt.tz_convert("UTC").dt.tz_localize(None)  # type: ignore
                        )
                export_df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Export knowledge base dataframes
            kb_model_fields = self.knowledge_base.model_fields_set
            for field_name in kb_model_fields:
                df = getattr(self.knowledge_base, field_name, None)
                if not isinstance(df, pd.DataFrame):
                    continue
                sheet_name = f"k_{field_name}"[:31]
                # Excel cannot handle tz-aware datetimes; drop tz only for export.
                tz_cols = df.select_dtypes(include=["datetimetz"]).columns
                export_df = df
                if len(tz_cols):
                    export_df = df.copy()
                    for col in tz_cols:
                        export_df[col] = (
                            export_df[col].dt.tz_convert("UTC").dt.tz_localize(None)  # type: ignore
                        )
                export_df.to_excel(writer, sheet_name=sheet_name, index=False)
