"""Apply reviewed YAML paragraph replacements to a separate manuscript copy."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
from xml.dom import minidom
from zipfile import ZipFile

import yaml
from pydantic import BaseModel, ConfigDict, Field

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class Replacement(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    find: str = Field(min_length=1)
    replace: str = Field(min_length=1)
    matches: int = Field(gt=0)
    rationale: str = Field(min_length=1)


class EditorialSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    owner: str
    topic: str
    command: str
    review_note: str
    replacements: list[Replacement]


def revise(source: Path, spec_path: Path, output: Path) -> None:
    if source.resolve() == output.resolve():
        raise ValueError("the source manuscript must not be overwritten")
    spec = EditorialSpec.model_validate(
        yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    )
    counts = [0] * len(spec.replacements)
    with ZipFile(source) as original:
        document = minidom.parseString(original.read("word/document.xml"))
        for paragraph in document.getElementsByTagNameNS(WORD_NS, "p"):
            runs = list(paragraph.getElementsByTagNameNS(WORD_NS, "t"))
            text = "".join(
                run.firstChild.nodeValue or "" for run in runs if run.firstChild
            )
            matches = [
                i
                for i, replacement in enumerate(spec.replacements)
                if text == replacement.find
            ]
            if len(matches) > 1:
                raise ValueError("overlapping editorial replacements")
            if not matches:
                continue
            index = matches[0]
            counts[index] += 1
            for run in runs:
                for child in list(run.childNodes):
                    run.removeChild(child)
            runs[0].appendChild(
                document.createTextNode(spec.replacements[index].replace)
            )
            runs[0].setAttribute("xml:space", "preserve")
        for replacement, count in zip(spec.replacements, counts, strict=True):
            if count != replacement.matches:
                raise ValueError(
                    f"expected {replacement.matches} matches, found {count}: {replacement.find[:80]}"
                )
        xml = document.toxml(encoding="utf-8")
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, "w") as revised:
            for item in original.infolist():
                revised.writestr(
                    item,
                    xml
                    if item.filename == "word/document.xml"
                    else original.read(item),
                )
    with ZipFile(output) as result:
        if result.testzip() is not None:
            raise ValueError("revised DOCX failed ZIP verification")
        minidom.parseString(result.read("word/document.xml"))
    output.with_suffix(".changes.yml").write_text(
        yaml.safe_dump(
            {
                "source_name": source.name,
                "source_sha256": sha256(source.read_bytes()).hexdigest(),
                "output_name": output.name,
                "output_sha256": sha256(output.read_bytes()).hexdigest(),
                "spec_sha256": sha256(spec_path.read_bytes()).hexdigest(),
                "applied_replacements": len(counts),
                "paragraphs_changed": sum(counts),
                "review_note": spec.review_note,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    print(
        f"Applied {len(counts)} reviewed replacements to {output}; original preserved."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--spec", type=Path, default=Path("docs/manuscript-reconciliation.yml")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    revise(args.source, args.spec, args.output)


if __name__ == "__main__":
    main()
