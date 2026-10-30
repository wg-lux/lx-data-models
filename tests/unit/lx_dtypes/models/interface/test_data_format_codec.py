from datetime import date
from enum import StrEnum
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from lx_dtypes.models.contracts.fhir_clinical import FhirObservation, FhirPatient
from lx_dtypes.models.interface.data_formats import (
    DataFormatError,
    DataFormatId,
    RecordValidationError,
    dump_record,
    dump_records,
    load_record,
    load_records,
    read_record,
    read_records,
    write_record,
    write_records,
)
from lx_dtypes.scripts.convert_records import main as convert_main


class Kind(StrEnum):
    BIOPSY = "biopsy"
    RESECTION = "resection"


class Measurement(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: str
    score: float | None = None


class Sample(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str
    count: int
    large: int
    accepted: bool
    collected: date
    kind: Kind
    tags: list[str]
    measurements: list[Measurement]
    note: str | None = None
    identifier: str = "unset"


SAMPLES = [
    Sample(
        name='comma, "quote" & <tag> ä =formula',
        count=-3,
        large=12345678901234567890,
        accepted=True,
        collected=date(2024, 1, 2),
        kind=Kind.BIOPSY,
        tags=["x", "1", "true"],
        measurements=[Measurement(code="c", score=1.5), Measurement(code="d")],
        identifier="007",
    ),
    Sample(
        name="=SUM(A1)",
        count=0,
        large=1,
        accepted=False,
        collected=date(2020, 5, 6),
        kind=Kind.RESECTION,
        tags=[],
        measurements=[],
        note="line one\nline two",
        identifier="",
    ),
]

TSV_SAFE = [SAMPLES[0], SAMPLES[1].model_copy(update={"note": "single line"})]


@pytest.mark.parametrize(
    "data_format",
    [
        DataFormatId.JSON,
        DataFormatId.YAML,
        DataFormatId.TOML,
        DataFormatId.XML,
        DataFormatId.CSV,
        DataFormatId.XLSX,
    ],
)
def test_records_round_trip(data_format: DataFormatId) -> None:
    content = dump_records(Sample, SAMPLES, data_format)
    assert load_records(Sample, content, data_format) == SAMPLES


def test_tsv_round_trip_and_rejects_line_breaks() -> None:
    content = dump_records(Sample, TSV_SAFE, "tsv")
    assert load_records(Sample, content, "tsv") == TSV_SAFE
    with pytest.raises(DataFormatError, match="tabs or line breaks"):
        dump_records(Sample, SAMPLES, "tsv")


def test_carriage_returns_are_preserved_or_refused() -> None:
    record = SAMPLES[1].model_copy(update={"note": "windows\r\nline"})
    for data_format in ("json", "yaml", "toml", "xml", "csv"):
        assert load_records(
            Sample, dump_records(Sample, [record], data_format), data_format
        ) == [record]
    with pytest.raises(DataFormatError, match="carriage returns"):
        dump_records(Sample, [record], "xlsx")


def test_empty_exports_round_trip() -> None:
    for data_format in ("json", "yaml", "toml", "xml", "csv", "tsv", "xlsx"):
        assert (
            load_records(Sample, dump_records(Sample, [], data_format), data_format)
            == []
        )


def test_empty_cells_apply_nullability_then_defaults() -> None:
    content = (
        b"name,count,large,accepted,collected,kind,tags,measurements,note,identifier\n"
        + (b'n,1,2,true,2024-01-01,biopsy,[],"[{""code"":""c""}]",,\n')
    )
    (record,) = load_records(Sample, content, "csv")
    assert record.note is None
    assert record.identifier == ""
    (defaulted,) = load_records(
        Sample,
        b"name,count,large,accepted,collected,kind,tags,measurements\nn,1,2,false,2024-01-01,biopsy,[],[]\n",
        "csv",
    )
    assert defaulted.identifier == "unset"


def _observation(identifier: str, **value: object) -> FhirObservation:
    return FhirObservation.model_validate(
        {
            "resourceType": "Observation",
            "id": identifier,
            "status": "final",
            "code": {
                "coding": [
                    {"system": "http://loinc.org", "code": "1-8", "display": "a & <b>"}
                ]
            },
            "subject": {"reference": "Patient/p1"},
            **value,
        }
    )


OBSERVATIONS = [
    _observation(
        "o1",
        valueQuantity={"value": 5, "unit": "mg"},
        component=[
            {"code": {"coding": [{"system": "s", "code": "c"}]}, "valueBoolean": True},
            {
                "code": {"coding": [{"system": "s", "code": "d"}], "text": "t"},
                "valueDecimal": 2.5,
            },
        ],
    ),
    _observation("o2", valueInteger=7),
]


@pytest.mark.parametrize("data_format", [DataFormatId.FHIR_JSON, DataFormatId.FHIR_XML])
@pytest.mark.parametrize("records", [OBSERVATIONS, OBSERVATIONS[1:]])
def test_fhir_bundles_round_trip(
    data_format: DataFormatId, records: list[FhirObservation]
) -> None:
    # A single repetition must still restore list cardinality from the schema.
    content = dump_records(FhirObservation, records, data_format)
    assert load_records(FhirObservation, content, data_format) == records


def test_fhir_xml_follows_hl7_encoding() -> None:
    content = dump_records(FhirObservation, OBSERVATIONS[1:], "fhir_xml").decode()
    assert '<Bundle xmlns="http://hl7.org/fhir">' in content
    assert "<resource>\n      <Observation>" in content
    assert '<valueInteger value="7"/>' in content
    assert '<display value="a &amp; &lt;b&gt;"/>' in content


def test_fhir_single_resource_and_type_checks() -> None:
    resource = b'{"resourceType": "Observation", "id": "o2", "status": "final", "code": {"coding": [{"system": "s", "code": "c"}]}, "subject": {"reference": "Patient/p1"}, "valueInteger": 7}'
    assert load_records(FhirObservation, resource, "fhir_json")[0].id == "o2"
    with pytest.raises(DataFormatError, match="not a Patient resource"):
        load_records(
            FhirPatient,
            dump_records(FhirObservation, OBSERVATIONS, "fhir_json"),
            "fhir_json",
        )
    with pytest.raises(DataFormatError, match="no resourceType"):
        dump_records(Sample, SAMPLES, "fhir_json")
    with pytest.raises(DataFormatError, match="literal resourceType"):
        load_records(Sample, resource, "fhir_json")


def test_validation_errors_omit_input_values() -> None:
    content = b'[{"name": "Jane Doe", "count": "not-a-number"}]'
    with pytest.raises(
        DataFormatError, match="Record 0 is not a valid Sample"
    ) as error:
        load_records(Sample, content, "json")
    assert "Jane Doe" not in str(error.value)
    assert "not-a-number" not in str(error.value)


def test_hostile_or_oversized_content_is_rejected() -> None:
    with pytest.raises(DataFormatError, match="aliases"):
        load_records(Sample, b"- &a {name: x}\n- *a\n", "yaml")
    entity = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY e "x">]><records><record/></records>'
    with pytest.raises(DataFormatError, match="unsafe XML"):
        load_records(Sample, entity, "xml")
    with pytest.raises(DataFormatError, match="import limit"):
        load_records(Sample, b"[]", "json", max_bytes=1)
    with pytest.raises(DataFormatError, match="UTF-8"):
        load_records(Sample, b"\xff", "csv")
    with pytest.raises(DataFormatError, match="duplicate columns"):
        load_records(Sample, b"name,name\n", "csv")


def test_mixed_record_types_are_rejected() -> None:
    with pytest.raises(DataFormatError, match="expected Sample"):
        dump_records(Sample, [Measurement(code="c")], "json")  # type: ignore[list-item]


def test_files_infer_format_and_refuse_clobbering(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "samples.xlsx"
    write_records(Sample, SAMPLES, target)
    assert read_records(Sample, target) == SAMPLES
    with pytest.raises(FileExistsError):
        write_records(Sample, SAMPLES, target)
    write_records(Sample, SAMPLES[:1], target, overwrite=True)
    assert read_records(Sample, target) == SAMPLES[:1]
    assert sorted(path.name for path in target.parent.iterdir()) == ["samples.xlsx"]


def test_cli_converts_and_validates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "observations.fhir.json"
    target = tmp_path / "observations.fhir.xml"
    write_records(FhirObservation, OBSERVATIONS, source)
    model = "lx_dtypes.models.contracts.fhir_clinical:FhirObservation"
    assert convert_main(["convert", "--model", model, str(source), str(target)]) == 0
    assert read_records(FhirObservation, target) == OBSERVATIONS
    assert convert_main(["validate", "--model", model, str(target)]) == 0
    assert "2 valid FhirObservation record(s)" in capsys.readouterr().out
    assert convert_main(["convert", "--model", model, str(source), str(target)]) == 1
    error = capsys.readouterr().err
    assert "Export destination already exists" in error
    assert ".lx-export-" not in error
    assert convert_main(["validate", "--model", "pathlib:Path", str(target)]) == 1
    assert convert_main(["formats"]) == 0
    assert (
        "xlsx\tapplication/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in capsys.readouterr().out
    )


@pytest.mark.parametrize(
    "data_format",
    [
        identifier
        for identifier in DataFormatId
        if identifier
        not in (DataFormatId.FHIR_JSON, DataFormatId.FHIR_XML, DataFormatId.TSV)
    ],
)
def test_single_record_round_trip(data_format: DataFormatId) -> None:
    content = dump_record(Sample, SAMPLES[0], data_format)
    assert load_record(Sample, content, data_format) == SAMPLES[0]


@pytest.mark.parametrize("data_format", [DataFormatId.FHIR_JSON, DataFormatId.FHIR_XML])
def test_single_fhir_resource_round_trip(data_format: DataFormatId) -> None:
    content = dump_record(FhirObservation, OBSERVATIONS[0], data_format)
    assert b"Bundle" not in content
    assert load_record(FhirObservation, content, data_format) == OBSERVATIONS[0]


def test_single_record_layouts_are_enforced(tmp_path: Path) -> None:
    with pytest.raises(DataFormatError, match="single record mapping"):
        load_record(Sample, b"[]", "json")
    with pytest.raises(DataFormatError, match="exactly one record, found 2"):
        load_record(Sample, dump_records(Sample, SAMPLES, "csv"), "csv")
    with pytest.raises(DataFormatError, match="root must be <record>"):
        load_record(Sample, dump_records(Sample, SAMPLES, "xml"), "xml")
    path = write_record(Sample, SAMPLES[1], tmp_path / "sample.yml")
    assert read_record(Sample, path) == SAMPLES[1]


def test_repeated_keys_are_rejected() -> None:
    with pytest.raises(DataFormatError, match="must not repeat keys"):
        load_record(Measurement, b'{"code": "a", "code": "b"}', "json")
    with pytest.raises(DataFormatError, match="must not repeat keys"):
        load_record(Measurement, b"code: a\ncode: b\n", "yaml")


def test_import_errors_neither_quote_nor_chain_content() -> None:
    with pytest.raises(DataFormatError) as malformed:
        load_record(Measurement, b"code: Jane Doe\n  bad: [\n", "yaml")
    assert "Jane Doe" not in str(malformed.value)
    assert "line 2" in str(malformed.value)
    assert malformed.value.__cause__ is None and malformed.value.__suppress_context__
    with pytest.raises(RecordValidationError) as invalid:
        load_record(Measurement, b'{"code": "Jane Doe", "score": "high"}', "json")
    assert "Jane Doe" not in str(invalid.value)
    assert invalid.value.__cause__ is None and invalid.value.__suppress_context__
