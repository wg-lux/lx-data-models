from enum import StrEnum


class DocumentType(StrEnum):
    report = "report"
    report_draft = "report_draft"
    report_final = "report_final"
    report_correction = "report_correction"
    histology_draft = "histology_draft"
    histology_final = "histology_final"
    referral = "referral"
    discharge = "discharge"


__all__ = ["DocumentType"]
