# Concept Relationships

This file describes the most important domain concepts in `lx-data-models` and how they are linked together.

Reading direction:

* `A -> B` means: `A` references `B` via names/IDs in a field. In YAML, these references are typically exact string matches.
* English domain terms are listed first, with the model or field names from the code shown in parentheses.
* Terminology objects define what is domain-permissible. Report and validator objects specify what is displayed and validated within a concrete report.

## Overall Picture

```text
Reports
+-- Examination
    +-- Examination Types
    +-- Findings
    |   +-- Finding Types
    |   +-- Classifications
    |   |   +-- Classification Types
    |   |   +-- Choices
    |   |       +-- Descriptors
    |   |           +-- Units
    |   +-- Interventions
    +-- Indications
        +-- Indication Types
        +-- Classifications
        +-- Interventions

Reports
+-- Report Sections
|   +-- Report Findings
|       +-- Findings
|       +-- Classifications
+-- Validators
    +-- Finding Validators
    +-- Classification Validators
    +-- Intervention Validators
    +-- Unit Validators
    +-- Examination Validators

```

## Mermaid Diagram

```text
---
config:
  theme: 'base'
  themeVariables:
    primaryColor: '#BB2528'
    primaryTextColor: '#fff'
    primaryBorderColor: '#7C0000'
    lineColor: '#F8B229'
    secondaryColor: '#006100'
    tertiaryColor: '#fff'
---
flowchart TD
  subgraph T["Terminology"]
    E["Examinations<br/>(examination)"]
    ET["Examination Types<br/>(examination_type)"]
    F["Findings<br/>(finding)"]
    FT["Finding Types<br/>(finding_type)"]
    I["Indications<br/>(indication)"]
    IT["Indication Types<br/>(indication_type)"]
    INT["Interventions<br/>(intervention)"]
    INTT["Intervention Types<br/>(intervention_type)"]
    C["Classifications<br/>(classification)"]
    CT["Classification Types<br/>(classification_type)"]
    CH["Choices<br/>(classification_choice)"]
    D["Descriptors<br/>(classification_choice_descriptor)"]
    U["Units<br/>(unit)"]
    UT["Unit Types<br/>(unit_type)"]
  end

  subgraph B["Reports and Validation"]
    RT["Reports<br/>(report_template)"]
    SEC["Report Sections<br/>(report_template_section)"]
    RF["Report Findings<br/>(report_finding)"]
    FV["Finding Validators<br/>(findings_validator)"]
    CV["Classification Validators<br/>(classification_validator)"]
    IV["Intervention Validators<br/>(intervention_validator)"]
    UV["Unit Validators<br/>(unit_validator)"]
    EV["Examination Validators<br/>(examination_validator)"]
  end


  RT -->|examination| E
  E -->|examination_types| ET
  E -->|findings| F
  E -->|indications| I

  F -->|finding_types| FT
  F -->|classifications| C
  F -->|interventions| INT
  F -->|caused_by_interventions| INT

  I -->|indication_types| IT
  I -->|classifications| C
  I -->|interventions| INT

  INT -->|intervention_types| INTT
  C -->|classification_types| CT
  C -->|classification_choices| CH
  CH -->|classification_choice_descriptors| D
  D -->|unit| U
  U -->|unit_types| UT

  RT -->|report_sections| SEC
  SEC -->|findings| RF
  RF -->|finding| F
  RF -->|classifications| C

  RT -->|validators.findings_validators| FV
  RT -->|validators.classification_validators| CV
  RT -->|validators.intervention_validators| IV
  RT -->|validators.unit_validators| UV
  RT -->|validators.examination_validators| EV

  FV -->|finding| F
  FV -->|condition.classification| C
  FV -->|then_requires| F
  FV -->|then_requires| C
  FV -->|then_requires| INT
  FV -->|then_requires| U

  CV -->|finding| F
  CV -->|classification| C
  CV -->|condition.classification| C
  CV -->|then_requires| F
  CV -->|then_requires| C
  CV -->|then_requires| INT
  CV -->|then_requires| U

  IV -->|finding| F
  IV -->|intervention| INT
  IV -->|condition.classification| C
  IV -->|then_requires| F
  IV -->|then_requires| C
  IV -->|then_requires| INT
  IV -->|then_requires| U

  UV -->|finding| F
  UV -->|classification| C
  UV -->|unit| U
  UV -->|condition.classification| C
  UV -->|then_requires| F
  UV -->|then_requires| C
  UV -->|then_requires| INT
  UV -->|then_requires| U

  EV -->|finding_validators| FV
  EV -->|examination_validators| EV

```

## Abstracted Terminology Diagram

This diagram shows only the terminology layer. It consolidates technical intermediate objects like `*_type` and highlights the main domain paths.

```text
---
config:
  theme: 'base'
  themeVariables:
    primaryColor: '#BB2528'
    primaryTextColor: '#fff'
    lineColor: '#000000ff'
---
flowchart LR
    %% Definition of Validator as a separate section
    subgraph Validation [Quality Assurance]
      VAL[Validator]
      AU[Notes / Advisories]
    end

    subgraph Pat [Patient-related]
      E["Examination"]
    end
    subgraph Core [Anamnesis / History]
      I["Indications"]
      F["Findings"]
      INT["Interventions"]
    end
    
    subgraph Metadata [Classifications]
      C["Classifications"]
      CH["Choices"]
      D["Descriptors"]
      U["Units"]
    end

    VS["Specific Validator"]

  

    %% Connections
    E --> F
    E --> I
    
    Core --> |Have Classifications| C
    F & I --> INT

    C --> CH
    CH --> D
    D --> U

    %% Validation (subtly visualized)
    VAL --> |Present?|Core
    VS --> |Conditions met?|Metadata
    VAL & Core --> VS


```

## Terminology Hierarchy

### Examinations (`examination`)

Examinations serve as the connecting level for examination types, findings, and indications.

* `examination.examination_types -> examination_type`
* Examination types group or categorize examinations.


* `examination.findings -> finding`
* Findings that can occur within this examination.


* `examination.indications -> indication`
* Indications that are allowed or relevant for this examination.



### Findings (`finding`)

Findings are terminological findings that can be documented within an examination.

* `finding.finding_types -> finding_type`
* Finding types group or categorize findings.


* `finding.classifications -> classification`
* Classifications describe the finding in more detail, for example morphology, localization, size, or severity.


* `finding.interventions -> intervention`
* Interventions that are available or permitted for this finding.


* `finding.caused_by_interventions -> intervention`
* Interventions that can cause this finding.



### Indications (`indication`)

Indications describe reasons, follow-up controls, or clinical contexts for examinations.

* `indication.indication_types -> indication_type`
* Indication types group or categorize indications.


* `indication.classifications -> classification`
* Classifications that describe an indication in more detail.


* `indication.interventions -> intervention`
* Interventions that may be relevant in the context of the indication.


* `examination.indications -> indication`
* An examination specifies which indications belong to it.



### Interventions (`intervention`)

Interventions are available procedures or measures.

* `intervention.intervention_types -> intervention_type`
* Intervention types group or categorize interventions.


* `finding.interventions -> intervention`
* Findings specify which interventions can be documented for them.


* `finding.caused_by_interventions -> intervention`
* Findings can reference interventions that caused them.


* `indication.interventions -> intervention`
* Indications can reference relevant interventions.



### Classifications (`classification`)

Classifications are structured dimensions such as morphology, localization, severity, size, or other selection and measurement dimensions.

* `classification.classification_types -> classification_type`
* Classification types group or categorize classifications.


* `classification.classification_choices -> classification_choice`
* Permitted choice values for this classification.


* `finding.classifications -> classification`
* Findings specify which classifications apply to them.


* `indication.classifications -> classification`
* Indications can have their own classifications.



### Choices (`classification_choice`)

Choices are atomic values from which classifications are constructed.

* `classification_choice.classification_choice_descriptors -> classification_choice_descriptor`
* Optional additional specifications for a choice value.


* `classification.classification_choices -> classification_choice`
* A classification defines its permitted choices.



### Descriptors (`classification_choice_descriptor`)

Descriptors describe additional details for choice values, such as numbers, text, boolean values, or multiple selections.

* `classification_choice_descriptor.classification_choice_descriptor_type`
* Type of descriptor, for example numeric, text, selection, or boolean.


* `classification_choice_descriptor.unit -> unit`
* Unit for numeric values.


* `classification_choice_descriptor.numeric_min` / `numeric_max`
* Boundaries for numeric values.


* `classification_choice_descriptor.text_max_length`
* Limit for text length.


* `classification_choice_descriptor.selection_options`
* Permitted options for selection descriptors.



### Units (`unit`)

Units are reusable units for numeric values such as lab values, dimensions, or durations.

* `unit.unit_types -> unit_type`
* Unit types group or categorize units.


* `unit.abbreviation`
* Abbreviation of the unit.


* `classification_choice_descriptor.unit -> unit`
* Descriptors can reference a unit.


* `unit_validator.unit -> unit`
* Unit validators check units within the context of a classification.



## Reports and Report Structure

### Reports (`report_template`)

Reports connect examination, report findings, and validators.

* `report_template.examination -> examination`
* The report applies to exactly one examination.


* `report_template.report_sections -> report_template_section`
* Report sections determine structure and sequence.


* `report_template.validators.examination_validators -> examination_validator`
* Groups of examination and finding rules.


* `report_template.validators.findings_validators -> findings_validator`
* Direct finding rules.


* `report_template.validators.classification_validators -> classification_validator`
* Direct classification rules.


* `report_template.validators.intervention_validators -> intervention_validator`
* Direct intervention rules.


* `report_template.validators.unit_validators -> unit_validator`
* Direct unit rules.



### Report Sections (`report_template_section`)

Report sections are not terminology concepts, but they organize report content.

* `report_template_section.findings -> report_finding`
* A section can reference reusable report findings.


* `report_template_section.findings -> inline finding requirement`
* Alternatively, a section can directly embed finding requirements.


* `report_template_section.fields`
* Optional fields for patient, examination, or anamnesis/history data.



### Report Findings (`report_finding`)

Report findings represent the report-centric view of terminology findings.

* `report_finding.finding -> finding`
* The domain finding.


* `report_finding.classifications[].classification -> classification`
* Classifications expected for this finding in the report.


* `report_finding.required`
* Flags whether the finding is expected in the template.


* `report_finding.multiple_allowed`
* Flags whether the finding may occur multiple times.



## Validator Hierarchy

### Finding Validators (`findings_validator`)

Finding validators check whether a finding is present, missing, or triggers further requirements under a specific condition.

* `findings_validator.finding -> finding`
* Target finding of the rule.


* `findings_validator.operator`
* `exists`, `missing`, or `condition`.


* `findings_validator.query.condition.any/all[].classification -> classification`
* Condition reads classification values of the target finding.


* `findings_validator.query.condition.then_requires[]`
* Can trigger additional `classification`, `finding`, `intervention`, or `unit` requirements.



### Classification Validators (`classification_validator`)

Classification validators check whether a classification for a finding is present, missing, or conditionally required.

* `classification_validator.finding -> finding`
* Target finding of the rule.


* `classification_validator.classification -> classification`
* Target classification of the rule.


* `classification_validator.operator`
* `exists`, `missing`, or `condition`.


* `classification_validator.precedence`
* `required` or `optional`.


* `classification_validator.query.condition.any/all[].classification -> classification`
* Condition reads classification values of the target finding.


* `classification_validator.query.condition.then_requires[]`
* Can trigger additional requirements for finding, classification, intervention, or unit.



### Intervention Validators (`intervention_validator`)

Intervention validators check whether an intervention for a finding is present, missing, or conditionally required.

* `intervention_validator.finding -> finding`
* Target finding of the rule.


* `intervention_validator.intervention -> intervention`
* Target intervention of the rule.


* `intervention_validator.operator`
* `exists`, `missing`, or `condition`.


* `intervention_validator.precedence`
* `required` or `optional`.


* `intervention_validator.query.condition.any/all[].classification -> classification`
* Condition reads classification values of the target finding.


* `intervention_validator.query.condition.then_requires[]`
* Can trigger additional requirements for finding, classification, intervention, or unit.



### Unit Validators (`unit_validator`)

Unit validators check whether a unit for a numeric or unit-related classification is present, missing, or conditionally required.

* `unit_validator.finding -> finding`
* Target finding of the rule.


* `unit_validator.classification -> classification`
* Target classification under which the unit is expected.


* `unit_validator.unit -> unit`
* Target unit of the rule.


* `unit_validator.operator`
* `exists`, `missing`, or `condition`.


* `unit_validator.precedence`
* `required` or `optional`.


* `unit_validator.query.condition.any/all[].classification -> classification`
* Condition reads classification values of the target finding.


* `unit_validator.query.condition.then_requires[]`
* Can trigger additional requirements for finding, classification, intervention, or unit.



### Examination Validators (`examination_validator`)

Examination validators group rules together. They do not directly validate individual payload values, but aggregate other validators.

* `examination_validator.finding_validators -> findings_validator`
* Groups atomic finding rules.


* `examination_validator.examination_validators -> examination_validator`
* Allows nested rule groups.


* `report_template.validators.examination_validators -> examination_validator`
* A report determines which rule groups are executed.



## Key Cross-Connections

* Examinations determine which findings and indications are allowed in context.
* Findings determine which classifications and interventions can be documented.
* Classifications determine which choices are allowed.
* Choices can have descriptors.
* Descriptors can reference units.
* Reports reference an examination and select report sections as well as validators.
* Report findings reference terminology findings and expected classifications.
* Validators check at runtime whether a filled-in report satisfies the requirements defined in the template.

## Model Names in Code

| Term (German / English) | Model Name in Code |
| --- | --- |
| Untersuchungen / Examinations | `examination` / `Examination` |
| Untersuchungstypen / Examination Types | `examination_type` / `ExaminationType` |
| Befunde / Findings | `finding` / `Finding` |
| Befundtypen / Finding Types | `finding_type` / `FindingType` |
| Indikationen / Indications | `indication` / `Indication` |
| Indikationstypen / Indication Types | `indication_type` / `IndicationType` |
| Interventionen / Interventions | `intervention` / `Intervention` |
| Interventionstypen / Intervention Types | `intervention_type` / `InterventionType` |
| Klassifikationen / Classifications | `classification` / `Classification` |
| Klassifikationstypen / Classification Types | `classification_type` / `ClassificationType` |
| Auswahlwerte / Choices | `classification_choice` / `ClassificationChoice` |
| Deskriptoren / Descriptors | `classification_choice_descriptor` / `ClassificationChoiceDescriptor` |
| Einheiten / Units | `unit` / `Unit` |
| Einheitentypen / Unit Types | `unit_type` / `UnitType` |
| Befund-Validatoren / Finding Validators | `findings_validator` / `FindingsValidator` |
| Klassifikations-Validatoren / Classification Validators | `classification_validator` / `ClassificationValidator` |
| Interventions-Validatoren / Intervention Validators | `intervention_validator` / `InterventionValidator` |
| Einheiten-Validatoren / Unit Validators | `unit_validator` / `UnitValidator` |
| Untersuchungs-Validatoren / Examination Validators | `examination_validator` / `ExaminationValidator` |
| Berichte / Reports | `report_template` / `ReportTemplate` |
| Berichtsabschnitte / Report Sections | `report_template_section` / `ReportTemplateSection` |
| Berichtsbefunde / Report Findings | `report_finding` / `ReportFinding` |

## Relevant Source Files

* `lx_dtypes/models/knowledge_base/examination/`
* `lx_dtypes/models/knowledge_base/finding/`
* `lx_dtypes/models/knowledge_base/indication/`
* `lx_dtypes/models/knowledge_base/intervention/`
* `lx_dtypes/models/knowledge_base/classification/`
* `lx_dtypes/models/knowledge_base/classification_choice/`
* `lx_dtypes/models/knowledge_base/classification_choice_descriptor/`
* `lx_dtypes/models/knowledge_base/unit/`
* `lx_dtypes/models/knowledge_base/report_template/`