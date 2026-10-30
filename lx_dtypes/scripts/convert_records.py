#!/usr/bin/env python3
"""Convert and validate Pydantic record files between registered data formats."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib import import_module
from pathlib import Path

from pydantic import BaseModel

from lx_dtypes.models.interface.data_formats import (
    DATA_FORMATS,
    DataFormatError,
    DataFormatId,
    read_records,
    write_records,
)
from lx_dtypes.models.interface.data_formats.codec import DEFAULT_MAX_BYTES


def load_model(reference: str) -> type[BaseModel]:
    """Resolve ``package.module:Class`` to a Pydantic model class."""
    module_name, separator, attribute_path = reference.partition(":")
    if not separator or not module_name or not attribute_path:
        raise ValueError(
            f"Model must be given as package.module:Class, got {reference!r}"
        )
    target: object = import_module(module_name)
    for attribute in attribute_path.split("."):
        target = getattr(target, attribute)
    if not isinstance(target, type) or not issubclass(target, BaseModel):
        raise TypeError(f"{reference} is not a Pydantic model class")
    return target


def _formats(_: argparse.Namespace) -> int:
    for data_format in DATA_FORMATS.values():
        kind = ("binary " if data_format.binary else "text ") + (
            "tabular" if data_format.tabular else "document"
        )
        extensions = ",".join(data_format.file_extensions)
        print(
            f"{data_format.identifier}\t{data_format.media_type}\t{extensions}\t{kind}"
        )
    return 0


def _convert(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    records = read_records(
        model, args.input, data_format=args.source_format, max_bytes=args.max_bytes
    )
    destination = write_records(
        model,
        records,
        args.output,
        data_format=args.target_format,
        overwrite=args.overwrite,
    )
    print(f"Wrote {len(records)} {model.__name__} record(s) to {destination}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    records = read_records(
        model, args.input, data_format=args.source_format, max_bytes=args.max_bytes
    )
    print(f"{args.input}: {len(records)} valid {model.__name__} record(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lx-dtypes-convert", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    choices = [identifier.value for identifier in DataFormatId]

    formats = commands.add_parser("formats", help="List supported formats")
    formats.set_defaults(func=_formats)

    for name, handler, help_text in (
        ("convert", _convert, "Validate records and write them in another format"),
        ("validate", _validate, "Validate every record in a file"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument(
            "--model", required=True, help="Pydantic model as package.module:Class"
        )
        command.add_argument(
            "--from",
            dest="source_format",
            choices=choices,
            help="Input format (default: extension)",
        )
        command.add_argument(
            "--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Input size limit"
        )
        command.add_argument("input", type=Path)
        if name == "convert":
            command.add_argument("output", type=Path)
            command.add_argument(
                "--to",
                dest="target_format",
                choices=choices,
                help="Output format (default: extension)",
            )
            command.add_argument(
                "--overwrite",
                action="store_true",
                help="Replace an existing output file",
            )
        command.set_defaults(func=handler)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (DataFormatError, ValueError, ImportError, AttributeError, OSError) as exc:
        print(f"lx-dtypes-convert: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
