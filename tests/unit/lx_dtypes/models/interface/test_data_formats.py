import pytest
from pydantic import ValidationError

from lx_dtypes.models.interface.data_formats import (
    DATA_FORMATS,
    DataFormat,
    DataFormatId,
    SyntaxRole,
    data_format_for_filename,
    data_format_for_media_type,
    get_data_format,
    syntax_table,
)


def test_every_identifier_is_registered() -> None:
    assert set(DATA_FORMATS) == set(DataFormatId)


def test_fhir_formats_extend_their_base_syntax() -> None:
    fhir_json = get_data_format("fhir_json")
    assert fhir_json.base_format is DataFormatId.JSON
    assert fhir_json.token(SyntaxRole.MAPPING_OPEN) == "{"
    assert fhir_json.token(SyntaxRole.RESOURCE_TYPE_KEY) == "resourceType"
    fhir_xml = get_data_format(DataFormatId.FHIR_XML)
    assert fhir_xml.token(SyntaxRole.NAMESPACE) == "http://hl7.org/fhir"
    assert not get_data_format("json").supports(SyntaxRole.RESOURCE_TYPE_KEY)


def test_unsupported_role_fails_explicitly() -> None:
    with pytest.raises(ValueError, match="no syntax for comment"):
        get_data_format("json").token(SyntaxRole.COMMENT)


def test_lookup_by_media_type_and_filename() -> None:
    assert (
        data_format_for_media_type("application/fhir+json; charset=utf-8").identifier
        is DataFormatId.FHIR_JSON
    )
    assert (
        data_format_for_filename("Patient.FHIR.JSON").identifier
        is DataFormatId.FHIR_JSON
    )
    assert data_format_for_filename("package.yml").identifier is DataFormatId.YAML
    with pytest.raises(ValueError):
        data_format_for_filename("notes.txt")
    with pytest.raises(ValueError):
        get_data_format("ini")


def test_tokens_are_immutable() -> None:
    with pytest.raises(TypeError):
        get_data_format("json").tokens[SyntaxRole.NULL] = "None"  # type: ignore[index]


def test_invalid_definitions_are_rejected() -> None:
    with pytest.raises(ValidationError):
        DataFormat(
            identifier=DataFormatId.JSON,
            media_type="application/json",
            file_extensions=(".json",),
            tokens={SyntaxRole.NULL: ""},
        )
    with pytest.raises(ValidationError):
        DataFormat(
            identifier=DataFormatId.JSON,
            media_type="application/json",
            file_extensions=("json",),
            tokens={SyntaxRole.NULL: "null"},
        )


def test_syntax_table_shape() -> None:
    table = syntax_table()
    assert list(table.index) == [identifier.value for identifier in DATA_FORMATS]
    assert list(table.columns) == [role.value for role in SyntaxRole]
    assert table.loc["yaml", "comment"] == "#"
    assert table.isna().loc["json", "comment"]


def test_formats_serialize_by_identifier() -> None:
    dumped = get_data_format("toml").model_dump(mode="json")
    assert dumped["identifier"] == "toml"
    assert dumped["tokens"]["key_value_separator"] == " = "
