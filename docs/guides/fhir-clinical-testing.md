# Clinical FHIR testing

The clinical FHIR contracts validate linked `Patient`, `Observation`, `Condition`,
and `DiagnosticReport` resources without persistence or Django models. Unknown
FHIR fields are retained so fixture parsing is lossless within the represented
resources.

## Supported boundary and compatibility

These models represent a patient-linked subset of FHIR R4, not a complete FHIR
validator or a claim of conformance to national implementation guides. Unknown
ordinary fields are retained; uninterpreted `modifierExtension` and `implicitRules`
are rejected because they may change clinical meaning. Unsupported Observation
value choices and absent-result semantics require an explicit profile adapter.
Do not treat retained extra fields as validated clinical content.

Numeric and boolean result fields reject coercion, nonfinite numbers, and
contradictory value choices. Bundle link resolution builds one index per operation,
rejects duplicate or unresolved targets and cross-patient reports, and performs no
network resolution. Relative identifiers and exact `fullUrl` aliases are supported;
ambiguous identifiers across servers require a host adapter. Resolving a bundle
does not establish consent, access rights, terminology validity, or clinical safety.

The finding/classification bridge in `ValidatorRuntime` is a component projection,
not a lossless round trip of complete clinical resources. It now rejects malformed
components instead of substituting `True`. Unitless numeric exports use
`valueQuantity`, a valid R4 choice; legacy `valueDecimal` remains accepted on input
for compatibility and must not be mistaken for a standard R4 Observation choice.
Exported Observation fragments now default to `preliminary`. Hosts with verified
finalization may explicitly call
`export_reported_findings_to_fhir_observations(..., status="final")`; they must
supply patient identity and the remaining resource context themselves.

Terminology export rejects names that map to duplicate normalized FHIR codes,
including collisions involving non-Latin names. Import rejects duplicate codes,
malformed concepts, and cyclic in-memory concept structures. Terminology domain
inference remains heuristic and requires review before clinical use.

See [the R4 Observation definition](https://hl7.org/fhir/R4/observation.html) for
the supported standard value choices. The production-readiness evidence and
remaining clinical acceptance gates are tracked in
`features/ProductionApplicationFoundations.yml`.

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
