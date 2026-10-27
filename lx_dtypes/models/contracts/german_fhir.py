"""German FHIR identifier systems and check-digit rules used by ePA profiles.

System URIs follow the HL7 Deutschland base profiles (``de.basisprofil.r4``) and
the KBV terminology canonicals referenced by ``de.gematik.epa.medication``.
"""

from __future__ import annotations

import re
from typing import Annotated, Final

from pydantic import AfterValidator

KVID_10_SYSTEM: Final = "http://fhir.de/sid/gkv/kvid-10"
IDENTIFIER_TYPE_DE_BASIS_SYSTEM: Final = (
    "http://fhir.de/CodeSystem/identifier-type-de-basis"
)
PZN_SYSTEM: Final = "http://fhir.de/CodeSystem/ifa/pzn"
ATC_DE_SYSTEM: Final = "http://fhir.de/CodeSystem/bfarm/atc"
ASK_SYSTEM: Final = "http://fhir.de/CodeSystem/ask"
ICD_10_GM_SYSTEM: Final = "http://fhir.de/CodeSystem/bfarm/icd-10-gm"
OPS_SYSTEM: Final = "http://fhir.de/CodeSystem/bfarm/ops"
KBV_DARREICHUNGSFORM_SYSTEM: Final = (
    "https://fhir.kbv.de/CodeSystem/KBV_CS_SFHIR_KBV_DARREICHUNGSFORM"
)
KBV_BMP_DOSIEREINHEIT_SYSTEM: Final = (
    "https://fhir.kbv.de/CodeSystem/KBV_CS_SFHIR_BMP_DOSIEREINHEIT"
)
UCUM_SYSTEM: Final = "http://unitsofmeasure.org"

_KVNR_PATTERN = re.compile(r"[A-Z][0-9]{9}")
_PZN_PATTERN = re.compile(r"[0-9]{8}")


def is_valid_kvnr(value: str) -> bool:
    """Validate the unchangeable 10-character part of a KVNR (GKV-Versichertennummer).

    The letter maps to its two-digit alphabet position; the resulting ten digits
    are weighted alternately 1 and 2, products above 9 contribute their digit sum,
    and the sum modulo 10 is the trailing check digit.
    """

    if not _KVNR_PATTERN.fullmatch(value):
        return False
    digits = f"{ord(value[0]) - ord('A') + 1:02d}{value[1:9]}"
    total = 0
    for index, digit in enumerate(digits):
        product = int(digit) * (1 if index % 2 == 0 else 2)
        total += product // 10 + product % 10
    return total % 10 == int(value[9])


def is_valid_pzn(value: str) -> bool:
    """Validate an 8-digit PZN (IFA modulo-11 check digit; remainder 10 is never issued)."""

    if not _PZN_PATTERN.fullmatch(value):
        return False
    remainder = sum(int(digit) * weight for weight, digit in enumerate(value[:7], 1))
    remainder %= 11
    return remainder != 10 and remainder == int(value[7])


def _validate_kvnr(value: str) -> str:
    if not is_valid_kvnr(value):
        raise ValueError(
            "KVNR must be an uppercase letter and 9 digits with a valid check digit"
        )
    return value


def _validate_pzn(value: str) -> str:
    if not is_valid_pzn(value):
        raise ValueError("PZN must be 8 digits with a valid check digit")
    return value


Kvnr = Annotated[str, AfterValidator(_validate_kvnr)]
Pzn = Annotated[str, AfterValidator(_validate_pzn)]


__all__ = [
    "ASK_SYSTEM",
    "ATC_DE_SYSTEM",
    "ICD_10_GM_SYSTEM",
    "IDENTIFIER_TYPE_DE_BASIS_SYSTEM",
    "KBV_BMP_DOSIEREINHEIT_SYSTEM",
    "KBV_DARREICHUNGSFORM_SYSTEM",
    "KVID_10_SYSTEM",
    "OPS_SYSTEM",
    "PZN_SYSTEM",
    "UCUM_SYSTEM",
    "Kvnr",
    "Pzn",
    "is_valid_kvnr",
    "is_valid_pzn",
]
