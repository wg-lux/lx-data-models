# Clinical FHIR testing

The clinical FHIR contracts validate linked `Patient`, `Observation`, `Condition`,
and `DiagnosticReport` resources without persistence or Django models. Unknown
FHIR fields are retained so fixture parsing is lossless within the represented
resources.

## Fast fixture tests

Run the database-free contract tests:

```bash
pytest tests/test_fhir_clinical.py
```

The transaction fixture is located at
`tests/fixtures/fhir/clinical-examination-transaction.json`. It verifies:

- required subjects and coded concepts;
- resolution of report results to Observations;
- resolution of clinical resources to the same Patient;
- preservation of standard top-level `Observation.value[x]`;
- the existing LXDM Observation component import/export path;
- rejection of unresolved references and malformed payloads.

## Import public HAPI test data as YAML

Fetch recent report graphs from HAPI R4 and validate every link before writing:

```bash
python scripts/import_fhir_clinical_yaml.py \
  --language de \
  --count 50
```

The default output is
`temp/generated_exports/hapi_clinical_import.yaml`. The importer sends the
selected language as `Accept-Language` and records it as `Bundle.language`.
Only reports whose Patient and every result Observation are present and valid
are included. Patient demographics, free-text narratives, identifiers, and
unrelated references are omitted because public test servers can contain
arbitrary user-submitted data; FHIR resource IDs are retained to preserve the
graph.

Use `--endpoint` for another R4 base URL and `--output` for another local path.
Server contents are volatile, so import counts can change between runs.

## Optional ephemeral HAPI server

The Compose profile runs HAPI FHIR with container-local storage. No host volume is
configured; removing the container removes its data.

```bash
docker compose \
  -f compose.fhir-test.yaml \
  --profile fhir-test \
  up -d --wait
```

Seed the same transaction fixture:

```bash
curl --fail-with-body \
  -H "Content-Type: application/fhir+json" \
  --data-binary @tests/fixtures/fhir/clinical-examination-transaction.json \
  http://localhost:8090/fhir
```

Exercise report/result inclusion:

```bash
curl --fail-with-body \
  -H "Accept: application/fhir+json" \
  "http://localhost:8090/fhir/DiagnosticReport?patient=example-patient&_include=DiagnosticReport:result"
```

Remove the ephemeral server:

```bash
docker compose \
  -f compose.fhir-test.yaml \
  --profile fhir-test \
  down --volumes
```

Set `FHIR_TEST_PORT` to use a host port other than `8090`.
