Public API
==========

The names on this page form the supported entry points of ``lx_dtypes``. Most
are re-exported lazily from the package root, so ``from lx_dtypes import
load_knowledge_base`` and the fully qualified imports below are equivalent.
Releases before ``1.0`` may change these names; ``CHANGELOG.md`` records every
breaking change.

Validation entry points
-----------------------

Non-raising validation returns a typed value together with a report of
advisory issues. See :doc:`../guides/cross-layer-validation` for error codes
and persistence boundaries.

.. automodule:: lx_dtypes.evaluation
   :members:
   :imported-members:
   :show-inheritance:

Knowledge-base loading
----------------------

.. automodule:: lx_dtypes.models.interface.KnowledgeBaseResolver
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.models.interface.data_roots
   :members: resolve_default_data_root, package_data_root

Terminology contracts
---------------------

.. automodule:: lx_dtypes.models.contracts.core_concepts
   :members:
   :show-inheritance:

Report templates
----------------

.. automodule:: lx_dtypes.models.knowledge_base.report_template.ReportTemplate
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.report_template.ReportFinding
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverage
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph
   :members:
   :show-inheritance:

Report-template validators
--------------------------

.. automodule:: lx_dtypes.models.knowledge_base.validators.FindingsValidator
   :members: FindingsValidator
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.validators.ClassificationValidator
   :members: ClassificationValidator
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.validators.InterventionValidator
   :members: InterventionValidator
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.validators.UnitValidator
   :members: UnitValidator
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.validators.ExaminationValidator
   :members: ExaminationValidator
   :show-inheritance:

.. automodule:: lx_dtypes.models.knowledge_base.validators.ValidatorRuntime
   :members: evaluate_findings_validator_runtime,
             evaluate_classification_validator_runtime,
             evaluate_intervention_validator_runtime,
             evaluate_unit_validator_runtime,
             evaluate_report_template_validators_runtime

.. automodule:: lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict
   :members:

Packages
--------

See :doc:`../guides/package-kinds` and
:doc:`../guides/dtypes-package-structure` for the authoring workflow.

.. automodule:: lx_dtypes.package_kinds
   :members:
   :show-inheritance:

.. automodule:: lx_dtypes.packages
   :members:
   :show-inheritance:
