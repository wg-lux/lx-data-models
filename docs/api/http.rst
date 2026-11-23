HTTP API
========

``lx_dtypes`` ships a `Django Ninja <https://django-ninja.dev/>`_ API in
:mod:`lx_dtypes.django.api.main`. Host applications mount it to read
terminology, author and validate report templates, and record patient
findings. This page is generated from the API's OpenAPI schema when the
documentation is built, so it always matches the code. The complete schema is
available for :download:`download as openapi.json <../_build/openapi/openapi.json>`.

Mounting
--------

Include ``lx_dtypes.django.urls`` to serve the API under ``/base_api/``, as
shown in the paths below, or mount ``lx_dtypes.django.api.main.api.urls``
under a prefix of your choice. Most routes need the host callbacks described
in :doc:`../guides/django-host-integration`, starting with
``LX_DTYPES_HOST_MODELS_MODULE``.

Authentication
--------------

The API does not authenticate users itself. Routes that require a user call
the host's ``authenticate_request_user`` callback and then a route-specific
authorization callback:

- **Report-template builder routes** require the ``report_template:read`` or
  ``report_template:write`` capability (``report_template_access_allowed``).
- **Patient-finding routes** require a user with access to the examination or
  finding (``patient_examination_access_allowed``,
  ``patient_finding_access_allowed``). Inaccessible objects return ``404``.
- **Terminology import and selection** require terminology write access
  (``terminology_write_access_allowed``) and return ``403`` when the host does
  not configure it.

Routes that say "No authentication is required" serve terminology and
validation only. The routes for a patient examination's stored LXDM record
and ``validate-from-ledger`` read patient data without checks of their own;
hosts must protect them.

Errors
------

Errors use one of two JSON bodies:

- ``{"detail": "..."}`` for report-template, graph, and terminology routes.
- ``{"code": "...", "message": "..."}`` for the examination, finding,
  indication, and patient-finding routes. ``code`` is stable, for example
  ``not-found``, ``invalid-finding``, or ``knowledge-base-identity-required``.

Each operation below lists the status codes it returns besides ``200``.

Knowledge-base versions
-----------------------

Routes that interpret clinical content work on one exact knowledge-base
version. Report-template and validation routes require an explicit
``version``. Catalog routes accept ``module_name`` together with
``module_version``, or take the version pinned on ``patient_examination_id``;
without either they use the active version. A payload whose
``knowledge_base_module`` or ``knowledge_base_version`` differs from the
request is rejected with ``409``.

Endpoint index
--------------

.. openapi-index::

Report languages
----------------

.. openapi-endpoints:: main

Report templates and validation
-------------------------------

Read published templates, author drafts in the report-template builder,
publish them, and validate examination data against a template's rules.
Validation results are advisory; see :doc:`../guides/cross-layer-validation`.

.. openapi-endpoints:: report_template_routes

.. rubric:: Models

.. openapi-models:: report_template_routes

Knowledge-base graph
--------------------

See :doc:`../guides/knowledge-base-graph-api` for the snapshot contract.

.. openapi-endpoints:: knowledge_base_graph_routes

Findings and patient findings
-----------------------------

Catalog routes list what the knowledge base allows for host examinations,
findings, and classifications. Patient-finding routes record and change
findings for one patient examination; each change refreshes the examination's
LXDM record in the same transaction.

.. openapi-endpoints:: findings_routes

.. rubric:: Models

.. openapi-models:: findings_routes

Indications
-----------

.. openapi-endpoints:: indications_routes

Examinations
------------

.. openapi-endpoints:: examinations_routes

Terminology bundles
-------------------

List, export, install, and activate terminology bundles. See
:doc:`../guides/terminology`.

.. openapi-endpoints:: terminology_routes

.. rubric:: Models

.. openapi-models:: terminology_routes
