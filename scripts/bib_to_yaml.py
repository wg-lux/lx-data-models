"""Convert BibTeX bibliographies into YAML data consumable by the loader."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import bibtexparser  # type: ignore[import]
import yaml
from bibtexparser.bparser import BibTexParser  # type: ignore[import]
from bibtexparser.customization import convert_to_unicode  # type: ignore[import]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "lx_dtypes" / "data" / "citations" / "sample_references.bib"
DEFAULT_TARGET_DIR = REPO_ROOT / "lx_dtypes" / "data" / "citations" / "data"
DEFAULT_OUTPUT_NAME = "sample_references.yaml"

MONTH_LOOKUP = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}

LATEX_REPLACEMENTS = {
    r"{\textgreater}": ">",
    r"{\textless}": "<",
    r"{\textendash}": "-",
    r"\&": "&",
    r"\%": "%",
    r"\_": "_",
}

IDENTIFIER_FIELDS = ("issn", "isbn", "pmid", "pmcid", "urldate", "shorttitle", "copyright", "note")

AUTHOR_SPLIT_RE = re.compile(r"\s+and\s+", flags=re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert BibTeX files into YAML for the data loader.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to the BibTeX file to convert.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help="Directory where the YAML file should be written.",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=DEFAULT_OUTPUT_NAME,
        help="File name to use for the generated YAML file.",
    )
    return parser.parse_args()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_text(value: str | None, *, preserve_newlines: bool = False) -> str | None:
    if not value:
        return None

    text = value.replace("\r\n", "\n").strip()
    for latex_token, replacement in LATEX_REPLACEMENTS.items():
        text = text.replace(latex_token, replacement)
    text = text.replace("{", "").replace("}", "")

    if preserve_newlines:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
    else:
        text = _normalize_whitespace(text)

    return text or None


def _split_authors(value: str | None) -> List[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return []
    return [author for author in (_normalize_whitespace(part) for part in AUTHOR_SPLIT_RE.split(cleaned)) if author]


def _extract_keywords(value: str | None) -> List[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return []
    keywords: List[str] = []
    for token in re.split(r"[,;]", cleaned):
        normalized = _normalize_whitespace(token)
        if normalized:
            keywords.append(normalized)
    return keywords


def _parse_year(value: str | None) -> int | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _normalize_month(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if lowered.isdigit():
        month_int = int(lowered)
        if 1 <= month_int <= 12:
            return f"{month_int:02d}"
    return MONTH_LOOKUP.get(lowered, cleaned)


def _build_identifiers(entry: Dict[str, Any]) -> Dict[str, str]:
    identifiers: Dict[str, str] = {}
    for field in IDENTIFIER_FIELDS:
        value = _clean_text(entry.get(field))
        if value:
            identifiers[field] = value
    return identifiers


def load_bib_entries(source: Path) -> List[Dict[str, Any]]:
    if not source.exists():
        raise FileNotFoundError(f"BibTeX file not found: {source}")

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode  # type: ignore[attr-defined]
    with source.open("r", encoding="utf-8") as handle:
        database: bibtexparser.bibdatabase.BibDatabase = bibtexparser.load(handle, parser=parser)  # type: ignore[attr-defined]

    entries: List[Dict[str, Any]] = []

    assert isinstance(entries, list)
    for entry in database.entries:  # type: ignore[attr-defined]
        assert isinstance(entry, dict)
        for k, _ in entry.items():  # type: ignore[attr-defined]
            assert isinstance(k, str)
        entries.append(entry)  # type: ignore[attr-defined]

    return entries


def convert_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    citation_key = entry.get("ID")
    if not citation_key:
        raise ValueError("Encountered BibTeX entry without an ID field.")

    title = _clean_text(entry.get("title"))
    if not title:
        raise ValueError(f"Citation '{citation_key}' is missing a title.")

    abstract = _clean_text(entry.get("abstract"), preserve_newlines=True)
    keywords = _extract_keywords(entry.get("keywords"))
    tags = sorted(set(keywords)) if keywords else []

    record: Dict[str, Any] = {
        "model": "citation",
        "name": citation_key,
        "citation_key": citation_key,
        "title": title,
        "abstract": abstract,
        "authors": _split_authors(entry.get("author")),
        "publication_year": _parse_year(entry.get("year")),
        "publication_month": _normalize_month(entry.get("month")),
        "journal": _clean_text(entry.get("journal")),
        "publisher": _clean_text(entry.get("publisher")),
        "volume": _clean_text(entry.get("volume")),
        "issue": _clean_text(entry.get("number") or entry.get("issue")),
        "pages": _clean_text(entry.get("pages")),
        "doi": _clean_text(entry.get("doi")),
        "url": _clean_text(entry.get("url")),
        "entry_type": entry.get("ENTRYTYPE"),
        "language": _clean_text(entry.get("language")),
        "keywords": keywords,
        "tags": tags,
    }

    if abstract:
        record["description"] = abstract

    identifiers = _build_identifiers(entry)
    if identifiers:
        record["identifiers"] = identifiers

    return {key: value for key, value in record.items() if value not in (None, [], {})}


def write_yaml(records: Iterable[Dict[str, Any]], target_dir: Path, file_name: str) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_name
    with target_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(list(records), handle, sort_keys=False, allow_unicode=True)
    return target_path


def main() -> None:
    args = parse_args()
    entries = load_bib_entries(args.source)
    if not entries:
        raise ValueError(f"No entries found in {args.source}")

    converted = sorted((convert_entry(entry) for entry in entries), key=lambda item: item["citation_key"])
    target_path = write_yaml(converted, args.target_dir, args.output_name)
    print(f"Wrote {len(converted)} citations to {target_path}")


if __name__ == "__main__":
    main()
