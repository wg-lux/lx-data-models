# Knowledge Base Core Models

## Type Hinting Patterns
### Many-to-Many Relationships
In the model where the relationship is defined, use the following pattern to ensure proper type hinting for Many-to-Many fields:
```python
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .finding import Finding

class Examination(KnowledgeBaseModel):
    findings: models.ManyToManyField["Finding", "Finding"] = models.ManyToManyField(
        "Finding",
        related_name="examinations",
        blank=True,
    )

```

In the related model, define a property to represent the reverse relationship:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .examination import Examination
    
class Finding(KnowledgeBaseModel):
    if TYPE_CHECKING:
        examinations: models.Manager["Examination"]

```

## One-to-Many / Foreign Key Relationships
In the model where the ForeignKey is defined, use the following pattern:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .patient_examination import PatientExamination

class PatientFinding(models.Model):
    patient_examination = models.ForeignKey("PatientExamination", on_delete=models.CASCADE, related_name="patient_findings")

    if TYPE_CHECKING:
        patient_examination: models.ForeignKey["PatientExamination"]
 
```

In the related model, define a property to represent the reverse relationship:
```python
if TYPE_CHECKING:
    from .patient_finding import PatientFinding
class PatientExamination(models.Model):
    if TYPE_CHECKING:
        patient_findings: models.QuerySet["PatientFinding"]

```

## Relationships
The core models define fundamental entities and their relationships within the system. Below is an overview of the key models and how they interrelate:

### Examination
Represents a medical examination without direct patient linkage.

Many-to-Many Relationships:
- ExaminationType
- Indication
- Finding

### Finding
Represents observations made during an examination.
Many-to-Many Relationships:
- FindingType
- Intervention
- Classification

### Indication
Represents reasons or motivations for conducting an examination.
Many-to-Many Relationships:
- IndicationType

### Intervention
Represents actions taken during or as a result of an examination.
Many-to-Many Relationships:
- InterventionType

### Classification
Represents categorizations or groupings of findings.
Many-to-Many Relationships:
- ClassificationType
- ClassificationChoice

### ClassificationChoice
Represents specific choices within a classification.
Many-to-Many Relationships:
- ClassificationChoiceDescriptor

### ClassificationChoiceDescriptor
Represents descriptors that provide additional context to classification choices.

Many-to-Many Relationships:
- Unit

### Unit
Represents measurement units used in Descripors.
