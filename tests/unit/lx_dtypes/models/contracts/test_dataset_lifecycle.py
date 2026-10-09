import pytest
from pydantic import ValidationError
from lx_dtypes.models.contracts.dataset_lifecycle import (
    DatasetCreate,
    DatasetDelete,
    DatasetSplit,
)
from lx_dtypes.models.contracts.ai_dataset import AIDataSetCreateContract


def test_clinical_dataset_has_no_training_model() -> None:
    assert DatasetCreate(name="Study").ai_model_type is None
    assert DatasetCreate(name="Study").dataset_type == "clinical"
    assert (
        AIDataSetCreateContract(name="Training").ai_model_type
        == "image_multilabel_classification"
    )
    with pytest.raises(ValidationError):
        DatasetCreate(name="Study", ai_model_type="image_multilabel_classification")


@pytest.mark.parametrize(
    "payload",
    [
        {"preview": "token"},
        {"preview": "token", "mode": "all"},
        {"preview": "", "mode": "memberships_only"},
    ],
)
def test_deletion_requires_explicit_supported_choice(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        DatasetDelete.model_validate(payload)


def test_split_cannot_put_one_patient_in_multiple_datasets() -> None:
    with pytest.raises(ValidationError):
        DatasetSplit.model_validate(
            {
                "partitions": [
                    {"name": "Train", "patients": [1, 2]},
                    {"name": "Test", "patients": [2]},
                ]
            }
        )
