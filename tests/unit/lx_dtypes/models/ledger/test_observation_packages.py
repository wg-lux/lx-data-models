"""Observation packages preserve contracts across imports, registries and storage."""

import importlib
import os
import subprocess
import sys
from datetime import UTC, datetime

import pytest

from lx_dtypes.models.ledger.p_electrical_application import (
    PElectricalApplication,
    PElectricalCurveComparison,
)
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset
from lx_dtypes.serialization import serialize_str_list


@pytest.mark.parametrize("module", ["p_time_offset", "p_electrical_application"])
def test_pydantic_packages_do_not_load_django(module: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import importlib
import sys
package = importlib.import_module('lx_dtypes.models.ledger.{module}')
models = importlib.import_module('lx_dtypes.models.ledger.{module}.Pydantic')
ddicts = importlib.import_module('lx_dtypes.models.ledger.{module}.DataDict')
from lx_dtypes.models.ledger.pydantic_main import ledger_models_lookup
for name, value in package.l_{module}_lookup.items():
    assert value is ledger_models_lookup[name]
    assert value is getattr(ddicts if name.endswith('DataDict') else models, name)
assert not any(name.startswith('django.') for name in sys.modules)
try:
    package.not_an_export
except AttributeError:
    pass
else:
    raise AssertionError('Unknown exports must raise AttributeError')
""",
        ],
        env={
            key: value
            for key, value in os.environ.items()
            if key != "DJANGO_SETTINGS_MODULE"
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture(
    params=["PTimeOffset", "PElectricalApplication", "PElectricalCurveComparison"]
)
def observation(
    request: pytest.FixtureRequest,
) -> PTimeOffset | PElectricalApplication | PElectricalCurveComparison:
    common = {
        "patient_examination": "exam-1",
        "knowledge_base_module": "example",
        "knowledge_base_version": "1.0.0",
    }
    if request.param == "PTimeOffset":
        anchor = {"kind": "electrosurgery", "time_base_num": 1, "time_base_den": 1000}
        return PTimeOffset.model_validate(
            {
                **common,
                "time_reference": "clock_offset",
                "evidence": {
                    "offset": {
                        "reference": {**anchor, "clock_id": "first", "ticks": -100},
                        "target": {**anchor, "clock_id": "second", "ticks": 150},
                    }
                },
            }
        )
    common["electrical_curve_profile"] = "profile"
    if request.param == "PElectricalApplication":
        return PElectricalApplication.model_validate(
            {
                **common,
                "measurement_source_sha256": "a" * 64,
                "session_id": "b" * 32,
                "clock_id": "c" * 32,
                "time_base_num": 1,
                "time_base_den": 1000,
                "sample_start_index": 0,
                "sample_end_index": 2,
                "start_timestamp": -1,
                "end_timestamp": 1,
                "started_at": datetime(2026, 1, 1, tzinfo=UTC),
                "curve": {
                    "quantities": ["power"],
                    "bin_values": [[5.0]],
                    "bin_sample_counts": [2],
                },
            }
        )
    return PElectricalCurveComparison.model_validate(
        {
            **common,
            "application": "current",
            "reference_applications": ["earlier-1", "earlier-2"],
            "result": {
                "design_terms": ["intercept"],
                "response_quantities": ["power"],
                "coefficients": [[5.0]],
                "residual_covariance": [[1.0]],
                "reference_row_count": 2,
                "reference_r_squared": [None],
                "section_rmse": [1.0],
                "bin_mahalanobis_squared": [1.0],
                "mean_mahalanobis_squared": 1.0,
                "threshold": 2.0,
                "verdict": "within_reference",
            },
        }
    )


@pytest.mark.django_db
@pytest.mark.parametrize("tags", [[], ["reviewed", "synthetic"]])
def test_django_roundtrip_and_registry(
    observation: PTimeOffset | PElectricalApplication | PElectricalCurveComparison,
    tags: list[str],
) -> None:
    from lx_dtypes.models.ledger.main import ledger_models_django_lookup

    package = importlib.import_module(type(observation).__module__.rsplit(".", 1)[0])
    adapter = getattr(package, type(observation).__name__ + "Django")
    assert adapter is ledger_models_django_lookup[type(observation).__name__]
    observation.tags = tags
    # The shared ORM base stores list-type CharFields as comma-separated strings.
    stored = adapter.sync_from_ddict(
        {**observation.ddict, "tags": serialize_str_list(tags)}
    )
    restored = type(observation).model_validate(stored.ddict)
    # created_at is assigned by the database on first insertion.
    assert restored.model_dump(
        mode="json", exclude={"created_at"}
    ) == observation.model_dump(mode="json", exclude={"created_at"})
    stored_again = adapter.sync_from_ddict(
        {**restored.ddict, "tags": serialize_str_list(tags)}
    )
    assert stored_again.pk == stored.pk
    assert adapter.objects.count() == 1
    assert type(observation).model_validate(stored_again.ddict) == restored
