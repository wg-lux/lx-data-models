#!/usr/bin/env python3
"""Generate a Mermaid diagram for FHIR-to-LXDM transformation patterns."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO, cast

from lx_dtypes.utils.fhir_lxdm_mapping import (
    mappings_from_document,
    standard_fhir_lxdm_mappings,
    write_mermaid,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", nargs="?", type=Path, help="JSON or YAML mapping spec")
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("fhir-lxdm-mapping.mmd")
    )
    parser.add_argument(
        "--title",
        default="FHIR resource graphs to LXDM clinical reporting elements",
    )
    args = parser.parse_args()

    if args.spec is None:
        mappings = standard_fhir_lxdm_mappings()
    else:
        with args.spec.open(encoding="utf-8") as stream:
            document = cast(
                object,
                json.load(stream)
                if args.spec.suffix.lower() == ".json"
                else _load_yaml(stream),
            )
        if not isinstance(document, Mapping):
            parser.error("mapping spec must contain a top-level object")
        mappings = mappings_from_document(cast(Mapping[str, Any], document))
    output = write_mermaid(args.output, mappings, title=args.title)
    print(output)
    return 0


def _load_yaml(stream: TextIO) -> object:
    """Load YAML only when a YAML spec is requested."""

    import yaml

    return yaml.safe_load(stream)


if __name__ == "__main__":
    raise SystemExit(main())
