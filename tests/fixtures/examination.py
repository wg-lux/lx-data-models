from pytest import fixture

from lx_dtypes.models.core.examination import Examination, ExaminationType
from lx_dtypes.models.core.finding import Finding
from lx_dtypes.models.core.indication import Indication


@fixture
def sample_examination_type() -> ExaminationType:
    return ExaminationType(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        name="endoscopy",
        tags=["sample", "test"],
    )


@fixture
def sample_examination(
    sample_examination_type: ExaminationType,
    sample_finding: Finding,
    sample_indication: Indication,
) -> Examination:
    examination = Examination(
        uuid="123e4567-e89b-12d3-a456-426614174001",
        name="Sample Examination",
        tags=["sample", "test"],
    )
    examination.types[sample_examination_type.name] = sample_examination_type
    examination.findings[sample_finding.name] = sample_finding
    examination.indications[sample_indication.name] = sample_indication
    return examination
