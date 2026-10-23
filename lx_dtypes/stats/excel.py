"""Literal, atomic XLSX exports for host-owned clinical datasets."""

import os
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd


def write_xlsx(
    file_path: Path,
    sheets: Iterable[tuple[str, pd.DataFrame]],
    *,
    overwrite: bool,
) -> None:
    """Write all sheets successfully before publishing the destination file.

    Text remains literal, large integers remain exact decimal text, and aware
    timestamps are exported as UTC without a timezone (Excel's representation).
    """
    if file_path.exists() and not overwrite:
        raise FileExistsError("Excel export destination already exists")
    with NamedTemporaryFile(dir=file_path.parent, suffix=".xlsx", delete=False) as temp:
        temporary_path = Path(temp.name)
    try:
        with pd.ExcelWriter(temporary_path, engine="openpyxl") as writer:
            names: set[str] = set()
            for name, frame in sheets:
                sheet_name = (
                    name
                    if len(name) <= 31
                    else f"{name[:22]}_{sha256(name.encode('utf-8')).hexdigest()[:8]}"
                )
                if sheet_name.casefold() in names:
                    raise ValueError(
                        "Excel export sheet names collide after truncation"
                    )
                names.add(sheet_name.casefold())
                writer.book.create_sheet(sheet_name)
                exported = frame.copy()
                for column in exported.columns:
                    _excel_scalar(column)
                for column in exported.select_dtypes(include=["datetimetz"]).columns:
                    exported[column] = (
                        exported[column].dt.tz_convert("UTC").dt.tz_localize(None)
                    )
                # Excel numbers carry only 15 significant decimal digits.
                for column in exported.columns:
                    exported[column] = exported[column].map(_excel_scalar)
                exported.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                for row in worksheet.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str):
                            # openpyxl otherwise treats '=' as a formula and
                            # strings such as '#N/A' as Excel error cells.
                            cell.data_type = "s"
            if not names:
                writer.book.create_sheet("empty")
        if overwrite:
            os.replace(temporary_path, file_path)
        else:
            # Atomic no-clobber publication also closes the exists/write race.
            os.link(temporary_path, file_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _excel_scalar(value: object) -> object:
    if isinstance(value, (str, list, tuple, dict)) and len(str(value)) > 32767:
        raise ValueError("Excel cell text exceeds the 32767 character limit")
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) >= 10**15:
        return str(value)
    return value
