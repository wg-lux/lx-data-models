"""Portable study evidence shared by hub and workbook transports."""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .cohort_definition import CohortDefinitionFields
from .package_snapshot import PackageSnapshot, restore_package_snapshot
from .study import StudyDefinition
from .study_collection import StudyCollectionRecord


class StudyExchangeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class StudyExchangeStudy(StudyExchangeModel):
    study_uuid: UUID
    definition: StudyDefinition


class StudyExchangeCohort(StudyExchangeModel):
    cohort_uuid: UUID
    study_uuid: UUID
    definition: CohortDefinitionFields


class StudyExchangePatientLink(StudyExchangeModel):
    patient_examination_uuid: UUID
    patient_uuid: UUID


class StudyExchangeBundle(StudyExchangeModel):
    """Current definitions and historical observations, with no host-local links.

    Dataset selection is deliberately not portable: receivers explicitly bind
    authorized local datasets. Historical collection definitions are retained
    independently of the current definitions, with local IDs removed.
    """

    contract_version: Literal["study_exchange_v1"] = "study_exchange_v1"
    studies: list[StudyExchangeStudy] = Field(max_length=1000)
    cohorts: list[StudyExchangeCohort] = Field(default_factory=list, max_length=1000)
    packages: list[PackageSnapshot] = Field(default_factory=list, max_length=100)
    collections: list[StudyCollectionRecord] = Field(
        default_factory=list, max_length=100000
    )
    patients: list[StudyExchangePatientLink] = Field(
        default_factory=list, max_length=100000
    )

    @model_validator(mode="after")
    def validate_closure(self) -> Self:
        from lx_dtypes.stats.study import validate_study_analysis
        from lx_dtypes.validation import assess_examination

        for identities in (
            [item.study_uuid for item in self.studies],
            [item.cohort_uuid for item in self.cohorts],
            [item.snapshot_id for item in self.packages],
            [item.record_uuid for item in self.collections],
            [item.patient_examination_uuid for item in self.patients],
        ):
            if len(identities) != len(set(identities)):
                raise ValueError("duplicate study exchange identity")
        studies = {item.study_uuid for item in self.studies}
        cohorts = {item.cohort_uuid: item for item in self.cohorts}
        patients = {
            item.patient_examination_uuid: item.patient_uuid for item in self.patients
        }
        snapshots = {item.snapshot_id: item for item in self.packages}
        knowledge_bases = {
            key: restore_package_snapshot(value) for key, value in snapshots.items()
        }
        by_identity = {
            (
                item.identity.knowledge_base_module,
                item.identity.knowledge_base_version,
            ): key
            for key, item in snapshots.items()
        }
        if len(by_identity) != len(snapshots):
            raise ValueError("conflicting snapshots for one package identity")
        for cohort in self.cohorts:
            if cohort.study_uuid not in studies:
                raise ValueError("cohort references an absent study")
        metadata = [item.definition.study_metadata for item in self.cohorts]
        for item in self.collections:
            if item.study_uuid not in studies:
                raise ValueError("collection references an absent study")
            if item.cohort_uuid is not None:
                cohort = cohorts.get(item.cohort_uuid)
                if cohort is None or cohort.study_uuid != item.study_uuid:
                    raise ValueError(
                        "collection references an absent or conflicting cohort"
                    )
            if item.cohort_definition is not None:
                if (
                    item.cohort_definition.study_id is not None
                    or item.cohort_definition.dataset_ids
                ):
                    raise ValueError("portable cohorts must not contain host-local IDs")
                metadata.append(item.cohort_definition.study_metadata)
            patient = patients.get(item.patient_examination_uuid)
            if patient is None or item.record.patient != str(patient):
                raise ValueError("ledger patient must match its persistent UUID link")
            snapshot = snapshots.get(item.package_snapshot_id)
            if (
                snapshot is None
                or snapshot.identity != item.evaluation.knowledge_base_identity
            ):
                raise ValueError("collection requires its exact package snapshot")
            assessed = assess_examination(
                knowledge_bases[item.package_snapshot_id],
                item.record.model_dump(mode="python"),
                template_name=item.report_template_name,
                language=item.language,
            )
            if assessed != item.evaluation:
                raise ValueError(
                    "collection evaluation differs from canonical assessment"
                )
        if set(patients) != {
            item.patient_examination_uuid for item in self.collections
        }:
            raise ValueError("patient links must match collected examinations exactly")
        for definition in metadata:
            for requirement in definition.terminology_requirements:
                if (requirement.module, requirement.version) not in by_identity:
                    raise ValueError(
                        "study metadata requires its exact package snapshot"
                    )
            for analysis in definition.analysis_definitions:
                validate_study_analysis(
                    analysis,
                    knowledge_bases[by_identity[(analysis.module, analysis.version)]],
                )
        return self
