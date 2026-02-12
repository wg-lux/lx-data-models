from typing import TypedDict, Union

from .ExaminationValidator import ExaminationValidator
from .ExaminationValidatorDataDict import ExaminationValidatorDataDict
from .FindingsValidator import FindingsValidator
from .FindingsValidatorDataDict import FindingsValidatorDataDict
from .ReportFinding import ReportFinding
from .ReportFindingDataDict import ReportFindingDataDict
from .ReportTemplate import ReportTemplate
from .ReportTemplateDataDict import ReportTemplateDataDict
from .ReportTemplateSection import ReportTemplateSection
from .ReportTemplateSectionDataDict import ReportTemplateSectionDataDict


class KbReportTemplateLookupType(TypedDict):
    ReportTemplate: type[ReportTemplate]
    ReportTemplateDataDict: type[ReportTemplateDataDict]
    ReportTemplateSection: type[ReportTemplateSection]
    ReportTemplateSectionDataDict: type[ReportTemplateSectionDataDict]
    ReportFinding: type[ReportFinding]
    ReportFindingDataDict: type[ReportFindingDataDict]
    FindingsValidator: type[FindingsValidator]
    FindingsValidatorDataDict: type[FindingsValidatorDataDict]
    ExaminationValidator: type[ExaminationValidator]
    ExaminationValidatorDataDict: type[ExaminationValidatorDataDict]


kb_report_template_lookup = KbReportTemplateLookupType(
    ReportTemplate=ReportTemplate,
    ReportTemplateDataDict=ReportTemplateDataDict,
    ReportTemplateSection=ReportTemplateSection,
    ReportTemplateSectionDataDict=ReportTemplateSectionDataDict,
    ReportFinding=ReportFinding,
    ReportFindingDataDict=ReportFindingDataDict,
    FindingsValidator=FindingsValidator,
    FindingsValidatorDataDict=FindingsValidatorDataDict,
    ExaminationValidator=ExaminationValidator,
    ExaminationValidatorDataDict=ExaminationValidatorDataDict,
)

kb_report_template_models = Union[
    ReportTemplate,
    ReportTemplateSection,
    ReportFinding,
    FindingsValidator,
    ExaminationValidator,
]

kb_report_template_ddicts = Union[
    ReportTemplateDataDict,
    ReportTemplateSectionDataDict,
    ReportFindingDataDict,
    FindingsValidatorDataDict,
    ExaminationValidatorDataDict,
]

__all__ = [
    "ReportTemplate",
    "ReportTemplateDataDict",
    "ReportTemplateSection",
    "ReportTemplateSectionDataDict",
    "ReportFinding",
    "ReportFindingDataDict",
    "FindingsValidator",
    "FindingsValidatorDataDict",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "KbReportTemplateLookupType",
    "kb_report_template_lookup",
    "kb_report_template_models",
    "kb_report_template_ddicts",
]
