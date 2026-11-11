"""Reporting vocabulary shared by wire contracts and knowledge-base models."""

from typing import Literal

ReportVerbosity = Literal["short", "standard", "detailed"]

__all__ = ["ReportVerbosity"]
