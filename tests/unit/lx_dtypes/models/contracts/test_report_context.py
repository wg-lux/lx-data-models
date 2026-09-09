from __future__ import annotations

from lx_dtypes.models.contracts import DocumentType, ReportContext


def test_report_context_accepts_document_type_enum() -> None:
    context = ReportContext(
        patient_examination_id=1,
        patient_id=2,
        document_type=DocumentType.report_draft,
        anonymized_text="validated text",
        source_pdf_id=3,
    )

    assert context.document_type == DocumentType.report_draft
    assert context.anonymized_text == "validated text"
