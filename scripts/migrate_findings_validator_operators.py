from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


OPERATOR_ALIASES = {
    "present": "exists",
    "absent": "missing",
    "not_exists": "missing",
    "not-exists": "missing",
    "not exists": "missing",
    "if": "condition",
}
FILE_EXTENSIONS = {".yaml", ".yml", ".json"}


@dataclass(frozen=True)
class Rewrite:
    path: tuple[str, ...]
    old: str
    new: str


def _is_findings_validator_record(node: dict[str, Any]) -> bool:
    model_name = str(node.get("model") or "").strip()
    if model_name == "findings_validator":
        return True
    query = node.get("query")
    return (
        "finding" in node
        and "operator" in node
        and isinstance(query, dict)
        and "operator" in query
    )


def _maybe_rewrite_operator(
    node: dict[str, Any],
    *,
    key: str,
    path: tuple[str, ...],
    rewrites: list[Rewrite],
) -> None:
    raw_value = node.get(key)
    if not isinstance(raw_value, str):
        return
    normalized = OPERATOR_ALIASES.get(raw_value.strip())
    if normalized is None or normalized == raw_value:
        return
    node[key] = normalized
    rewrites.append(Rewrite(path=path + (key,), old=raw_value, new=normalized))


def _rewrite_findings_validator(
    node: dict[str, Any], path: tuple[str, ...], rewrites: list[Rewrite]
) -> None:
    _maybe_rewrite_operator(node, key="operator", path=path, rewrites=rewrites)
    query = node.get("query")
    if isinstance(query, dict):
        _maybe_rewrite_operator(
            query, key="operator", path=path + ("query",), rewrites=rewrites
        )


def rewrite_document(document: Any) -> tuple[Any, list[Rewrite]]:
    rewrites: list[Rewrite] = []
    rewritten = _rewrite_node(document, (), rewrites)
    return rewritten, rewrites


def _rewrite_node(node: Any, path: tuple[str, ...], rewrites: list[Rewrite]) -> Any:
    if isinstance(node, dict):
        if _is_findings_validator_record(node):
            cloned = dict(node)
            _rewrite_findings_validator(cloned, path, rewrites)
            for key, value in list(cloned.items()):
                if key in {"query"}:
                    continue
                cloned[key] = _rewrite_node(value, path + (str(key),), rewrites)
            return cloned
        return {
            key: _rewrite_node(value, path + (str(key),), rewrites)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [
            _rewrite_node(value, path + (str(index),), rewrites)
            for index, value in enumerate(node)
        ]
    return node


def _iter_target_files(paths: Iterable[Path]) -> Iterable[Path]:
    for root in paths:
        if root.is_file():
            if root.suffix in FILE_EXTENSIONS:
                yield root
            continue
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in FILE_EXTENSIONS:
                yield path


def _load_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def _dump_file(path: Path, document: Any) -> str:
    if path.suffix == ".json":
        return json.dumps(document, indent=2, ensure_ascii=True) + "\n"
    return yaml.safe_dump(document, sort_keys=False, allow_unicode=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    rewritten_any = False
    for path in _iter_target_files(args.paths):
        loaded = _load_file(path)
        rewritten, rewrites = rewrite_document(loaded)
        if not rewrites:
            continue
        rewritten_any = True
        rendered = ", ".join(
            f"{'.'.join(rewrite.path)}: {rewrite.old!r}->{rewrite.new!r}"
            for rewrite in rewrites
        )
        print(f"{path}: {rendered}")
        if args.write:
            path.write_text(_dump_file(path, rewritten), encoding="utf-8")

    if args.check and rewritten_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
