# Record import and export formats

Owner: lx_dtypes maintainers. This guide owns validated import and export of
lists of one Pydantic model through `lx_dtypes.models.interface.data_formats`.
Multi-table projections of complete clinical datasets are covered by
[standardized CSV exports](standardized-csv-export.md). Host authorization,
storage locations and patient selection remain the host's responsibility.

## Formats

Every format has a stable `DataFormatId`, a media type, file extensions and a
syntax table (`syntax_table()` returns it as a DataFrame).

| Identifier | Media type | Extensions | Layout |
| --- | --- | --- | --- |
| `json` | `application/json` | `.json` | List of record objects |
| `yaml` | `application/yaml` | `.yaml`, `.yml` | List of record objects |
| `toml` | `application/toml` | `.toml` | `[[records]]` tables; `None` fields omitted |
| `xml` | `application/xml` | `.xml` | `<records><record><field name type>` |
| `fhir_json` | `application/fhir+json` | `.fhir.json` | `collection` Bundle |
| `fhir_xml` | `application/fhir+xml` | `.fhir.xml` | `collection` Bundle, HL7 XML encoding |
| `csv` | `text/csv` | `.csv` | Header row, one row per record |
| `tsv` | `text/tab-separated-values` | `.tsv` | Header row, one row per record |
| `xlsx` | Office Open XML spreadsheet | `.xlsx` | `records` sheet, one row per record |

## Python API

```python
from pathlib import Path

from lx_dtypes.models.contracts.fhir_clinical import FhirObservation
from lx_dtypes.models.interface.data_formats import (
    dump_records,
    load_records,
    read_records,
    write_records,
)

content = dump_records(FhirObservation, observations, "fhir_xml")
restored = load_records(FhirObservation, content, "fhir_xml")

write_records(FhirObservation, observations, Path("export/observations.xlsx"))
rows = read_records(FhirObservation, Path("export/observations.xlsx"))
```

- Export dumps each record in JSON mode by alias. Every record must be exactly
  the given model class.
- Import validates each record through the model's JSON validator, so strict
  models accept ISO dates, enums and UUIDs as they would from a JSON API.
- File functions infer the format from the longest matching extension, so
  `.fhir.json` is FHIR JSON. Pass `data_format=` to override it.
- `write_records` publishes atomically and refuses an existing file unless
  `overwrite=True`.
- Imports are limited to `DEFAULT_MAX_BYTES` (64 MiB) unless `max_bytes=` is set.
- Failures raise `DataFormatError`; content that parses but fails model
  validation raises its subclass `RecordValidationError`. Messages name the
  record index, field location and reason, never the input value, and are not
  chained to parser or validation exceptions that could quote it.
- JSON objects and YAML mappings with repeated keys are rejected, because
  parsers disagree on which value wins.

## Single records

`dump_record`, `load_record`, `write_record` and `read_record` handle one record
per file, for example a metadata sidecar:

| Formats | Single-record layout |
| --- | --- |
| JSON, YAML, TOML | The document is the record mapping |
| XML | `<record>` root with typed `<field>` children |
| FHIR JSON, FHIR XML | One resource, not a Bundle |
| CSV, TSV, XLSX | A header row and exactly one data row |

```python
from lx_dtypes.models.interface.data_formats import RecordValidationError, read_record

try:
    metadata = read_record(SidecarPayload, sidecar_path, max_bytes=1024 * 1024)
except RecordValidationError:
    ...  # readable, but not a valid SidecarPayload
```

## Text cells and FHIR XML

CSV, TSV and XLSX cells, and FHIR XML primitives, are text. The model's JSON
schema restores numbers, booleans and list cardinality; unresolved values are
left for model validation to reject. In tabular formats:

- nested values are compact JSON text;
- an empty cell is `None` when the field is nullable, `""` for string fields,
  and otherwise absent so the field default applies;
- unknown extra fields become sorted trailing columns.

FHIR import accepts a `collection` Bundle or a single resource whose
`resourceType` matches the model's literal `resourceType`. FHIR export omits
nulls and empty arrays, as FHIR JSON requires.

## Refused content

The codec refuses content instead of changing it:

- TSV cells containing tabs or line breaks; use CSV.
- XLSX cells containing carriage returns, which workbook XML cannot preserve.
- TOML arrays containing `None`, since TOML has no null.
- YAML anchors and aliases, XML document type declarations and entities.

Spreadsheet text is written literally, including values beginning with `=`.
The XLSX writer stores them as text, not formulas. Hosts offering CSV downloads
to spreadsheet users own any formula-injection policy.

## Command line

The wheel installs `lx-dtypes-convert`:

```bash
lx-dtypes-convert formats
lx-dtypes-convert convert --model lx_dtypes.models.contracts.fhir_clinical:FhirObservation \
  observations.fhir.json observations.xlsx
lx-dtypes-convert validate --model package.module:Model records.csv --from csv
```

`--model` accepts any importable Pydantic model, including host models. The
command exits with status 1 and a one-line message on any import, validation
or file error.
