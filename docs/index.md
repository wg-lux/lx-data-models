# lx-dtypes Documentation

`lx-dtypes` provides models, terminology, and validation for clinical research.
These pages explain the concepts, show examples, and describe integration.

## Reader roadmap

No prior knowledge of the project is needed. Follow these steps or go straight
to the topic you need.

| Step | Read or try | What you will learn |
| --- | --- | --- |
| 1. Understand the model | [Data-model concept map](guides/data-model-concept-map.md) | How terminology, patient records, and reports fit together. Start at Level 0. |
| 2. Run a small example | [Project README](https://github.com/wg-lux/lx-data-models/blob/main/README.md) | Follow the quick start to load a shipped knowledge base and inspect validation findings. |
| 3. Try package authoring | [Your first study package](guides/dtypes-package-structure.md#start-here-your-first-study-package) | Copy, inspect, and register a synthetic YAML package. |
| 4. Choose an integration | [Validation](guides/cross-layer-validation.md), [Django](guides/django-host-integration.md), or [FHIR](guides/fhir-lxdm-mapping-diagrams.md) | Apply the models in a host application. |
| 5. Contribute what you learn | [Contributing](https://github.com/wg-lux/lx-data-models/blob/main/CONTRIBUTING.md) | Report a confusing step, improve an example, or prepare a code change. |

For terminology work, continue with [knowledge-base authoring](guides/knowledge-base-authoring.md).
For reporting, use [report-template authoring](guides/report-template-authoring.md).
The [API reference](api/index.md) provides details for individual models and functions.

## Project direction

The package is in alpha. Public imports may change before `1.0`; release notes
record breaking changes. Check the
[issue tracker](https://github.com/wg-lux/lx-data-models/issues) for open work
and discuss larger proposals there before implementation.

Useful starting points include clearer examples, reproducible bug reports,
terminology validation, and host integration. Choose a small task you can verify.
Documentation and domain feedback are welcome alongside code contributions.

## Contents
```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
```

```{toctree}
:maxdepth: 2
:caption: Guides

agent_context
guides/pydantic-cheatsheet
guides/dates-and-times
guides/typing_conventions
guides/package_boundary
guides/data-model-concept-map
guides/cross-layer-validation
guides/django-host-integration
guides/standardized-csv-export
medication_plan_specification_summary
guides/fhir-clinical-testing
guides/epa-fhir-compatibility
guides/fhir-lxdm-mapping-diagrams
guides/concept-relationships
guides/knowledge-base-authoring
guides/terminology
guides/dtypes-package-structure
guides/kb-yaml-linting
guides/knowledge-base-contract-migration
guides/knowledge-base-graph-api
guides/runtime-output-vs-canonical-ddict
guides/report-concept-coverage
guides/report-template-authoring
guides/report-template-infrastructure
guides/report-template-graph-validation
guides/report-template-findings-validator-migration
```

## Quick Links
- Project repository: https://github.com/wg-lux/lx-data-models
- Issue tracker: https://github.com/wg-lux/lx-data-models/issues
- Python Package Index: https://pypi.org/project/lx-dtypes/

If a topic is missing or a step is unclear, open an issue with what you tried
and what you expected.
