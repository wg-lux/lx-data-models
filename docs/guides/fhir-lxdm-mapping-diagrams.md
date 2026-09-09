# FHIR resource graphs → LXDM clinical reporting elements

The package includes a Mermaid generator for documenting context-dependent
transformations between FHIR resource graphs and LXDM clinical reporting
elements. Generate the built-in transformation patterns with:

```shell
lx-dtypes-fhir-lxdm-diagram --output docs/diagrams/fhir_lxdm_mapping.mmd
```

The output is a Mermaid `flowchart`. FHIR resources feed named adapter
patterns, and each pattern constructs or decomposes one or more LXDM
elements. The intermediate pattern makes aggregation and decomposition
explicit and avoids implying one-to-one semantic equivalence.

Custom mappings use a JSON or YAML document with a top-level `patterns` list:

```yaml
patterns:
  - name: Finding-related intervention
    sources:
      - FHIR.Procedure
      - FHIR.MedicationAdministration
      - FHIR.Device
      - FHIR.Specimen
    targets:
      - LXDM.PFindingIntervention
    rules:
      - source: Procedure.code/bodySite/reasonReference
        target: Intervention concept and finding relation
        note: primary performed-action context
      - source: MedicationAdministration.medication[x]/effective[x]
        target: Medication detail
        note: only when medication was administered
```

The Python API is available from `lx_dtypes.utils.fhir_lxdm_mapping`.
