# Terminology Level and Instance Level

The following distinguishes a definitional terminology level from a
patient-specific instance level. This separation is necessary so that
terminology standards can be modelled and validated in a structured way,
independently of individual documentation cases, and later applied to concrete
examinations.

**Examinations** are, at the terminology level, defined examination types that
specify which finding types, indications, and documentation rules are
permitted or required in a given context. At the instance level, examinations
are concrete procedures performed on a patient that check for the presence of
possible findings.

**Findings** are, at the terminology level, defined finding types that can
occur within certain examination types. They specify which classifications and
treatments may be linked to them. At the instance level, findings are
patient-specific observations or biological entities documented during a
concrete examination.

**Classifications** are defined descriptive dimensions of a finding, for
example its location, morphology, structure, or other clinical
characteristics. They are modelled as structured feature spaces, not only as
free-text entries. At the instance level, they are assigned to a concrete
finding and evaluated for completeness and plausibility. A classification can
have one or more classification types and one or more classification choices.

**Classification types** specify what kind of classification is present. They
include location, morphology, laboratory, and laboratory reference, which
document the context of the measurement and its capture.

**Classification choices** are the permitted values of a classification. They
can be modelled as nominal, ordinal, or binary. Their structure is defined at
the terminology level and validated when patient-specific data is entered.

**Requirements** are formalized rules that define under which conditions a
finding, a classification, or a documentation is considered complete or
compliant. They can refer to medication, previous illnesses, examination
contexts, laboratory parameters, or findings already documented, among other
things, and are applied to concrete instances.

**Treatments** are, at the terminology level, defined intervention types that
can be linked to certain finding types. At the instance level, they are
concrete measures carried out in connection with a patient-specific finding.
In defined cases, they can trigger follow-up findings or further documentation
obligations.
