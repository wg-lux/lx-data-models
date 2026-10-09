# Build a study report template

Owner: lx_dtypes maintainers. This is the canonical beginner guide for designing
study data capture with report templates. You can start with a text editor or
spreadsheet; programming knowledge is not needed to complete the study worksheet.

A **report template** describes what staff should record during an examination
and which missing or inconsistent answers the application should flag. By the
end of this guide, you will have a study worksheet, a draft template, and example
records your technical colleague can use to check and install it.

A complete study also needs participant selection, follow-up linkage, and an
analysis plan. These are separate from the report template. The steps below
identify where each belongs.

## 1. Describe your study before editing files

Copy this worksheet into your protocol or a spreadsheet. Replace the example
with your own decisions. The example is for learning, not a recommended protocol.

| Decision | Example | Your study |
| --- | --- | --- |
| Research question | Compare outcomes after two resection techniques | Fill in |
| Who or what is included? | Lesions meeting the protocol's eligibility criteria | Fill in |
| One row in the analysis represents… | One attempted resection of one lesion | Fill in |
| Groups to compare | EMR and ESD | Fill in |
| Main outcome | Recurrence at the agreed follow-up assessment | Fill in |
| When is each outcome measured? | At the visit specified by the protocol | Fill in |
| Other information needed | Lesion size, technique, complications | Fill in |
| How are repeat visits linked? | Case, lesion, and index-examination identifiers | Fill in |
| How are missing answers handled? | Distinguish unknown, not assessed, and not applicable | Fill in |
| Who approves changes? | Named study lead and data manager | Fill in |

For each outcome, write its exact definition, measurement method, time window,
and analysis approach in the protocol. Decide how to handle a change of technique
or an incomplete procedure. A field called “success” alone does not define a
reproducible outcome.

For a worked study specification, see the
[ColoReg capture and analysis example](coloreg-resection-study.yml). It explains
which observations and links support the study and which filters the host
application must implement separately.

## 2. List the questions staff must answer

Make one row for every measurement or question. Group rows into sections such
as “Index examination”, “Resection”, and “Follow-up”.

| Question | Answer format | When required? | Can it repeat? |
| --- | --- | --- | --- |
| Maximum lesion diameter | Number in millimetres | For each included lesion | One per lesion |
| Resection technique | Choice from the approved list | For each resection attempt | One per attempt |
| Snare type | Choice from the approved list | When the protocol requires a snare assessment | One per attempt |
| Electrosurgery settings | Documented settings | When a diathermic snare was used | One per attempt |
| Follow-up outcome | Choice from the approved list | At each applicable follow-up visit | One per visit and lesion |

Write units and allowed answers explicitly. Decide whether “unknown”, “not
assessed”, and “not applicable” are legitimate answers for each question; they
have different meanings. Ask the technical colleague to check which choices
already exist before adding new ones.

For repeated lesions or visits, record the identifiers needed to connect them.
A patient identifier alone cannot distinguish two lesions in the same patient.
The application must check those links; entering an identifier as text does not
by itself establish a valid relationship.

## 3. Choose an existing template as your starting point

Ask your administrator which template and terminology version are installed.
For the current ColoReg example, the package is `coloreg@0.3.0` and its template
is `coloreg_colonoscopy`, version `2.0.0`. Package and template versions are
separate numbers. Older packages can contain different questions and rules.

Compare your question list with the existing template. Mark each question as
“reuse”, “change”, or “add”. Reuse established definitions when their meaning
matches your protocol. Keep an editable copy under a new study package identity
when creating a different study; retain the original release for existing data.

The [example package](../../lx_dtypes/data/terminology/report_template_examples/report_templates.yaml)
shows the file format. The [package guide](dtypes-package-structure.md) provides
a small training package for learning how files are loaded.

## 4. Translate your questions into a draft template

These are the few file terms you need:

| File term | Plain-language meaning |
| --- | --- |
| `finding` | The observation being recorded, such as a polyp or resection attempt |
| `classification` | A question or measurement about that observation |
| `classification_choice` | An allowed answer to that question |
| `report_finding` | Which observation and questions this template presents |
| `report_template_section` | A group of observations shown together |
| `findings_validator` | A rule that checks the recorded answers |
| `report_template` | The sections and rules selected for this report |
| `config.yaml` | The list of files and existing terminology packages to load |

Display labels can be readable words. Internal identifiers such as
`coloreg_snare_type` must match the existing terminology exactly. Keep spaces,
indentation, and field names unchanged when editing YAML, the text format used
for these definitions.

Work in an editable study directory with this layout:

```text
my_study/
  config.yaml            # package name, version, dependencies, and file list
  report_templates.yml   # questions, sections, and the report template
  validators.yml         # checks on recorded answers
```

For this exercise, put the following in `config.yaml`. `depends_on` tells the
loader to reuse the existing ColoReg definitions. Ask your administrator to
provide the intended ColoReg release and its dependencies.

```yaml
name: my_study
version: '0.1.0'
modules: []
depends_on:
- coloreg
data:
  files:
  - ./report_templates.yml
  - ./validators.yml
```

The folder and package name are both `my_study`. Choose a unique name for your
real study. Patient observations go into the application, not these definition
files. See the [package instructions](dtypes-package-structure.md) when adapting
the manifest to another terminology package.

For example, this excerpt presents two existing ColoReg questions about a
resection. It belongs in `report_templates.yml`:

```yaml
- model: report_finding
  name: my_study_resection_questions
  finding: coloreg_polyp_resection
  required: false
  multiple_allowed: true
  classifications:
  - classification: coloreg_snare_type
    required: true
  - classification: coloreg_electrosurgery_settings
    required: false
```

Read it as: “A report may contain several resection observations. For a recorded
resection, request the snare type. Settings are required only in the circumstances
defined by the rule below.” The settings field stays optional here so it is not
requested unconditionally.

Below that record, add the section and template to the same file:

```yaml
- model: report_template_section
  name: my_study_resection_section
  position: 0
  section_kind: findings
  findings:
  - my_study_resection_questions

- model: report_template
  name: my_study_report
  examination: colonoscopy
  report_sections:
  - my_study_resection_section
  validators:
    findings_validators:
    - my_study_hot_snare_requires_settings
```

This connects the questions to the “colonoscopy” examination and selects the
rule you will define next. `position: 0` makes this the first section. For more
sections, use unique names, increasing positions, and add their names to
`report_sections`. `required: false` on the observation permits its absence;
if your protocol requires at least one such observation, add a presence rule.

## 5. Write the checks in ordinary language first

For every rule, specify a trigger and an expected answer. For example:
**“If a diathermic snare was used, electrosurgery settings must be documented.”**
The technical form below belongs in `validators.yml`:

```yaml
- model: findings_validator
  name: my_study_hot_snare_requires_settings
  finding: coloreg_polyp_resection
  operator: condition
  query:
    finding: coloreg_polyp_resection
    operator: condition
    condition:
      any:
      - classification: coloreg_snare_type
        comparator: in
        values: [coloreg_snare_diathermic, coloreg_snare_both]
      then_requires:
      - kind: classification
        name: coloreg_electrosurgery_settings
```

Read `any` as “at least one of these conditions” and `in` as “the answer is one
of these choices”. The rule name already appears in the template's
`validators.findings_validators` list above. Add new rule names there when you
add new rules to `validators.yml`.

Together, these examples form a draft for preview and review. Production use
also needs the coverage metadata and publication described in step 7.
A rule can be present in a file without being selected by your template.
Writing “required when a hot snare is used” in a description alone does not create
a check. Technical rule names must agree exactly across files.

## 6. Try example records and review the messages

Use invented records to check the draft together with your technical colleague.
For the snare rule, these are the expected results:

| Example record | Expected feedback from this rule |
| --- | --- |
| Cold snare | No settings requirement |
| Diathermic snare, no settings | Settings are missing |
| Diathermic snare, settings recorded | Requirement satisfied |
| Snare type unanswered | Warning: the rule cannot yet decide whether settings are needed |
| Two resections, only one with a diathermic snare | Check the conditional requirement separately for each resection |

Also try an absent optional observation, a missing required measurement, and
multiple lesions with repeat visits. Check the displayed questions, units,
answer choices, and section order against your worksheet.

A warning can mean “we need more information to evaluate this rule”. It does
not necessarily mean the answer entered was wrong. Other template checks may
still report missing fields even when this particular rule passes.

## 7. Prepare the study for use

Before installation, review these items with the study lead and administrator:

- The questions, allowed answers, units, and rules match the approved protocol.
- Every outcome has a definition and a way to find its supporting observations.
- The technical colleague has added the required **coverage matrix**: a list
  connecting each study concept to its recorded value and checks. See the
  [coverage contract](report-concept-coverage.md) for the file fields.
- The example records produce the agreed feedback, including incomplete records.
- The administrator has validated, registered, selected, and published the
  intended package/template versions in the application.
- Participant eligibility, cohort/dataset setup, visit linkage, and analysis
  are configured separately. See the [study setup instructions](knowledge-base-authoring.md#dataset-and-live-cohort-setup-templates)
  and [package guide](dtypes-package-structure.md). Template rules do not
  automatically apply statistical filters or create an analysis dataset.

Give the administrator your worksheet, draft files, expected example results,
and named approval owner. Record the versions used for collection. Publish a
new version when definitions or rules change, and retain earlier versions so
historical observations can still be interpreted correctly.

## Technical reference: where ColoReg feedback comes from

Researchers can stop above. This source trace is for the colleague investigating
messages or checking the YAML connections.


In the current source, `coloreg@0.3.0` defines `coloreg_colonoscopy` template
version `2.0.0`. Its `report_templates.yaml` **names all 13 resection and
follow-up validators**, at the end under `validators.findings_validators`.
It references record names, not `resection_validators.yml` as a file.
The empty `coverage_concepts[].validator_names` lists are coverage metadata;
they do not disable template validators.

The process is:

1. `lx_dtypes/data/terminology/coloreg/config.yaml` selects both
   `report_templates.yaml` and `data/resection_validators.yml` in `data.files`.
   The loader parses their records into one KB and loads declared dependencies.
2. `KnowledgeBase.evaluate_report_template_validators()` selects the named
   rules. It also calls `get_report_template_classification_validators()`:
   every section classification with `required: true` gets an implicit `exists`
   validator unless an explicit validator covers that finding/classification.
   ColoReg currently generates **23** of these, despite an empty
   `validators.classification_validators` list. Implicit rules run only for
   finding types present in the payload; an optional, absent finding does not
   trigger them.
3. `FindingsCapturePage.vue` in lx-annotate schedules validation after a
   350 ms debounce. `frontend/src/api/reportTemplatesApi.ts` sends the typed
   draft to `POST /report-templates/{module}/{template}/validate?version=...`
   under the host's API prefix. The route in
   `lx_dtypes/django/api/report_template_routes.py` loads the exact registered
   module/version, evaluates the rules, and adds server-side `concept_coverage`.
4. `ValidatorRuntime.py` evaluates conditional rules per finding occurrence.
   For `coloreg_hot_snare_requires_settings`, a diathermic or combined snare
   requires `coloreg_electrosurgery_settings`. Missing settings produces
   `missing_required_classification`; a missing snare choice produces
   `missing_data_requirement` at warning level because applicability cannot
   yet be decided. That warning also makes the validator's `ok` false.
   Intervention requirements can produce `missing_required_reference`.
5. The frontend normalizes the response and stores `flow.lastTemplateValidation`.
   `reportingValidationPresentation.ts` groups backend issues by finding for
   display; the validation panel receives the same result. Separately,
   `fieldMessages()` in the page creates local required-field text from the
   merged finding/template classifications. These messages need no named
   findings validator. Backend missing classifications are also grouped by
   finding type, so field feedback can appear on multiple instances of that type.

To identify a particular issue, inspect the validation response's `code`,
`validator_kind`, `validator_name`, and `details.occurrence_index` where present.
A name beginning `implicit_classification_validator__` comes from a required
template classification. A `coloreg_*` findings rule resolves in
`data/resection_validators.yml`. Local field text has no backend issue record.
Coverage results are a separate evidence contract, described in the
[coverage guide](report-concept-coverage.md).

This trace describes checked-out source, not a running deployment. Historical
ColoReg packages differ: `0.2.0` has only the polyp section. Confirm the request
identity and registered source before comparing a browser response with YAML;
editing this checkout does not update a host's registered release or cache.

## Technical reference: validation commands

From the repository root, check the existing ColoReg package with:

```sh
uv run python -m lx_dtypes.scripts.validate_report_templates --module coloreg
uv run pytest tests/unit/lx_dtypes/models/interface/test_report_template_runtime_execution.py -q
```

For a new package, supply `--data-root` pointing to a tree containing it and
its dependencies, and use its module name. Read the reported blocking issues;
a successful exit alone does not establish that a draft is ready for publication.
Preview the resolved template and exercise passing, failing, and incomplete
typed `PExamination` payloads. See the
[infrastructure guide](report-template-infrastructure.md) for runtime APIs and
the [package guide](dtypes-package-structure.md) for registration and deployment.
