"""Read bounded, data-only study setup YAML without filesystem or database writes."""

from __future__ import annotations

import yaml

from lx_dtypes.models.contracts.study_setup import StudySetupDefinition

MAX_SETUP_BYTES = 1_048_576
MAX_SETUP_DEPTH = 32
MAX_SETUP_EVENTS = 50_000


def _check_mapping_keys(node: yaml.Node) -> None:
    if isinstance(node, yaml.MappingNode):
        seen: set[str] = set()
        for key, value in node.value:
            if (
                not isinstance(key, yaml.ScalarNode)
                or key.tag != "tag:yaml.org,2002:str"
            ):
                raise ValueError(
                    "setup mapping keys must be strings; merge keys are prohibited"
                )
            if key.value in seen:
                raise ValueError(
                    f"duplicate mapping key at line {key.start_mark.line + 1}, "
                    f"column {key.start_mark.column + 1}"
                )
            seen.add(key.value)
            _check_mapping_keys(value)
    elif isinstance(node, yaml.SequenceNode):
        for child in node.value:
            _check_mapping_keys(child)


def parse_setup_yaml(raw: str) -> object:
    """Validate one UTF-8 document; aliases and merge keys are forbidden.

    Hosts must also bound request/file reads before constructing ``raw``. This
    function does not authorize callers, provision rows, or evaluate membership.
    """
    if len(raw) > MAX_SETUP_BYTES or len(raw.encode("utf-8")) > MAX_SETUP_BYTES:
        raise ValueError("study setup exceeds the 1 MiB input limit")
    try:
        depth = 0
        for count, event in enumerate(yaml.parse(raw, Loader=yaml.SafeLoader), start=1):
            if count > MAX_SETUP_EVENTS:
                raise ValueError("study setup exceeds the event limit")
            if isinstance(event, yaml.AliasEvent):
                # The YAML is structurally valid but violates the accepted input policy.
                raise ValueError(  # noqa: TRY004
                    "YAML aliases are prohibited in study setups"
                )
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                depth += 1
                if depth > MAX_SETUP_DEPTH:
                    raise ValueError("study setup exceeds the nesting limit")
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                depth -= 1
        loader = yaml.SafeLoader(raw)
        try:
            node = loader.get_single_node()
            if node is None:
                raise ValueError("study setup must contain a document")
            _check_mapping_keys(node)
            payload: object = loader.construct_document(node)
        finally:
            loader.dispose()
    except yaml.YAMLError as exc:
        raise ValueError("invalid study setup YAML syntax or tag") from exc
    return payload


def parse_study_setup_yaml(raw: str) -> StudySetupDefinition:
    return StudySetupDefinition.model_validate(parse_setup_yaml(raw))
