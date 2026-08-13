from typing import TypedDict, Union

from .DataDict import ReportDataDict, SerializedReportDataDict
from .Pydantic import Report, SerializedReport


class LReportLookupType(TypedDict):
    Report: type[Report]
    ReportDataDict: type[ReportDataDict]
    SerializedReportDataDict: type[SerializedReportDataDict]
    SerializedReport: type[SerializedReport]


l_report_lookup = LReportLookupType(
    Report=Report,
    ReportDataDict=ReportDataDict,
    SerializedReportDataDict=SerializedReportDataDict,
    SerializedReport=SerializedReport,
)
l_report_models = Union[Report]
l_report_ddicts = Union[ReportDataDict, SerializedReportDataDict]

__all__ = [
    "Report",
    "SerializedReport",
    "ReportDataDict",
    "SerializedReportDataDict",
    "LReportLookupType",
    "l_report_lookup",
    "l_report_models",
    "l_report_ddicts",
]
