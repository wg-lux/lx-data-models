"""XML writers built from the syntax table and hardened XML readers.

Generic XML carries an explicit JSON type on every value so it round-trips
losslessly. FHIR XML follows the HL7 JSON/XML correspondence: primitives sit
in a ``value`` attribute, element ``id`` and extension ``url`` are attributes,
repetitions are repeated elements, contained resources are wrapped in their
property element, and ``_name`` primitive extensions merge into ``name``.
"""

import json
import re
from collections.abc import Mapping
from xml.etree.ElementTree import Element, tostring

from defusedxml.ElementTree import fromstring

from ._schema import JsonValue
from .base import FHIR_XML_FORMAT, XML_FORMAT, DataFormat, SyntaxRole

FHIR_NAMESPACE = FHIR_XML_FORMAT.token(SyntaxRole.NAMESPACE)
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
_INVALID_XML_CHARACTERS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff￾￿]")
_XML_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")
_RESOURCE_TYPE = re.compile(r"[A-Z][A-Za-z]*")


class MarkupError(ValueError):
    pass


class _XmlWriter:
    def __init__(self, data_format: DataFormat) -> None:
        self._format = data_format
        self._lines = [data_format.token(SyntaxRole.DECLARATION)]

    def _tag(self, name: str, attributes: Mapping[str, str], *, empty: bool) -> str:
        if not _XML_NAME.fullmatch(name):
            raise MarkupError(f"Not a valid XML element name: {name!r}")
        token = self._format.token
        quote = token(SyntaxRole.STRING_QUOTE)
        parts = [token(SyntaxRole.ELEMENT_OPEN), name]
        for key, value in attributes.items():
            parts.append(
                f" {key}{token(SyntaxRole.ATTRIBUTE_VALUE_SEPARATOR)}{quote}{_escape(value, attribute=True)}{quote}"
            )
        parts.append(
            token(SyntaxRole.EMPTY_ELEMENT_CLOSE if empty else SyntaxRole.ELEMENT_CLOSE)
        )
        return "".join(parts)

    def _end(self, name: str) -> str:
        token = self._format.token
        return (
            f"{token(SyntaxRole.END_TAG_OPEN)}{name}{token(SyntaxRole.ELEMENT_CLOSE)}"
        )

    def empty(self, depth: int, name: str, attributes: Mapping[str, str]) -> None:
        self._lines.append("  " * depth + self._tag(name, attributes, empty=True))

    def text(
        self, depth: int, name: str, attributes: Mapping[str, str], text: str
    ) -> None:
        if text == "":
            self.empty(depth, name, attributes)
            return
        self._lines.append(
            "  " * depth
            + self._tag(name, attributes, empty=False)
            + _escape(text, attribute=False)
            + self._end(name)
        )

    def open(self, depth: int, name: str, attributes: Mapping[str, str]) -> None:
        self._lines.append("  " * depth + self._tag(name, attributes, empty=False))

    def close(self, depth: int, name: str) -> None:
        self._lines.append("  " * depth + self._end(name))

    def raw(self, depth: int, markup: str) -> None:
        self._lines.append("  " * depth + markup)

    def content(self) -> bytes:
        return ("\n".join(self._lines) + "\n").encode("utf-8")


def _escape(value: str, *, attribute: bool) -> str:
    if _INVALID_XML_CHARACTERS.search(value):
        raise MarkupError("Text contains characters that XML 1.0 cannot represent")
    escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Parsers normalise CR (and whitespace in attributes); character references survive.
    escaped = escaped.replace("\r", "&#13;")
    if attribute:
        escaped = (
            escaped.replace('"', "&quot;").replace("\t", "&#9;").replace("\n", "&#10;")
        )
    return escaped


def _scalar_text(value: bool | float | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value, allow_nan=False)
    return value


def _parse(content: bytes) -> Element:
    try:
        return fromstring(content, forbid_dtd=True)
    except Exception as exc:  # defusedxml raises several unrelated exception types.
        raise MarkupError(f"Malformed or unsafe XML: {exc}") from exc


def _local(element: Element) -> tuple[str | None, str]:
    if element.tag.startswith("{"):
        namespace, _, name = element.tag[1:].partition("}")
        return namespace, name
    return None, element.tag


# Generic typed XML


def dump_xml(records: list[dict[str, JsonValue]]) -> bytes:
    writer = _XmlWriter(XML_FORMAT)
    writer.open(0, "records", {})
    for record in records:
        writer.open(1, "record", {})
        for key, value in record.items():
            _write_typed(writer, 2, "field", {"name": key}, value)
        writer.close(1, "record")
    writer.close(0, "records")
    return writer.content()


def _write_typed(
    writer: _XmlWriter,
    depth: int,
    name: str,
    attributes: dict[str, str],
    value: JsonValue,
) -> None:
    if value is None:
        writer.empty(depth, name, {**attributes, "type": "null"})
    elif isinstance(value, bool):
        writer.text(depth, name, {**attributes, "type": "boolean"}, _scalar_text(value))
    elif isinstance(value, int):
        writer.text(depth, name, {**attributes, "type": "integer"}, _scalar_text(value))
    elif isinstance(value, float):
        writer.text(depth, name, {**attributes, "type": "number"}, _scalar_text(value))
    elif isinstance(value, str):
        writer.text(depth, name, {**attributes, "type": "string"}, value)
    elif isinstance(value, list):
        if not value:
            writer.empty(depth, name, {**attributes, "type": "array"})
            return
        writer.open(depth, name, {**attributes, "type": "array"})
        for item in value:
            _write_typed(writer, depth + 1, "item", {}, item)
        writer.close(depth, name)
    else:
        if not value:
            writer.empty(depth, name, {**attributes, "type": "object"})
            return
        writer.open(depth, name, {**attributes, "type": "object"})
        for key, item in value.items():
            _write_typed(writer, depth + 1, "field", {"name": key}, item)
        writer.close(depth, name)


def dump_xml_record(record: dict[str, JsonValue]) -> bytes:
    writer = _XmlWriter(XML_FORMAT)
    writer.open(0, "record", {})
    for key, value in record.items():
        _write_typed(writer, 1, "field", {"name": key}, value)
    writer.close(0, "record")
    return writer.content()


def load_xml_record(content: bytes) -> dict[str, JsonValue]:
    root = _parse(content)
    if root.tag != "record":
        raise MarkupError("XML record document root must be <record>")
    return _read_fields(root)


def load_xml(content: bytes) -> list[dict[str, JsonValue]]:
    root = _parse(content)
    if root.tag != "records":
        raise MarkupError("XML document root must be <records>")
    records: list[dict[str, JsonValue]] = []
    for record in root:
        if record.tag != "record":
            raise MarkupError(f"Unexpected element <{record.tag}> in <records>")
        records.append(_read_fields(record))
    return records


def _read_fields(element: Element) -> dict[str, JsonValue]:
    fields: dict[str, JsonValue] = {}
    for child in element:
        name = child.get("name")
        if child.tag != "field" or name is None:
            raise MarkupError("Object members must be <field name=...> elements")
        if name in fields:
            raise MarkupError(f"Duplicate XML field: {name!r}")
        fields[name] = _read_typed(child)
    return fields


def _read_typed(element: Element) -> JsonValue:
    kind = element.get("type")
    text = element.text or ""
    if kind in ("array", "object") and text.strip():
        raise MarkupError(f"<{element.tag}> of type {kind} must not contain text")
    if kind not in ("array", "object") and len(element):
        raise MarkupError(f"<{element.tag}> of type {kind} must not contain elements")
    if kind == "null":
        return None
    if kind == "string":
        return text
    if kind == "boolean" and text in ("true", "false"):
        return text == "true"
    if kind in ("integer", "number"):
        try:
            number = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MarkupError(f"Invalid {kind} value: {text!r}") from exc
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise MarkupError(f"Invalid {kind} value: {text!r}")
        if kind == "integer" and not isinstance(number, int):
            raise MarkupError(f"Invalid integer value: {text!r}")
        return number
    if kind == "array":
        items: list[JsonValue] = []
        for child in element:
            if child.tag != "item":
                raise MarkupError("Array members must be <item> elements")
            items.append(_read_typed(child))
        return items
    if kind == "object":
        return _read_fields(element)
    raise MarkupError(f"Unknown or invalid XML value type: {kind!r}")


# FHIR XML


def dump_fhir_xml(resource: dict[str, JsonValue]) -> bytes:
    writer = _XmlWriter(FHIR_XML_FORMAT)
    _write_resource(writer, 0, resource, root=True)
    return writer.content()


def _write_resource(
    writer: _XmlWriter, depth: int, resource: Mapping[str, JsonValue], *, root: bool
) -> None:
    resource_type = resource.get("resourceType")
    if not isinstance(resource_type, str) or not _RESOURCE_TYPE.fullmatch(
        resource_type
    ):
        raise MarkupError("FHIR resources require a valid resourceType")
    attributes = {"xmlns": FHIR_NAMESPACE} if root else {}
    writer.open(depth, resource_type, attributes)
    _write_members(writer, depth + 1, resource, in_resource=True, extension=False)
    writer.close(depth, resource_type)


def _attribute_members(
    value: Mapping[str, JsonValue], *, in_resource: bool, extension: bool
) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for key in ("id",) if not in_resource else ():
        if isinstance(value.get(key), str):
            attributes[key] = str(value[key])
    if extension and isinstance(value.get("url"), str):
        attributes["url"] = str(value["url"])
    return attributes


def _write_members(
    writer: _XmlWriter,
    depth: int,
    value: Mapping[str, JsonValue],
    *,
    in_resource: bool,
    extension: bool,
) -> None:
    attribute_keys = set(
        _attribute_members(value, in_resource=in_resource, extension=extension)
    )
    for key, item in value.items():
        if key == "resourceType" or key in attribute_keys:
            continue
        if key.startswith("_"):
            if key[1:] in value:
                continue
            key, item, extensions = key[1:], None, item
        else:
            extensions = value.get(f"_{key}")
        if isinstance(item, list) or isinstance(extensions, list):
            items = item if isinstance(item, list) else []
            metadata = extensions if isinstance(extensions, list) else []
            for index in range(max(len(items), len(metadata))):
                _write_element(
                    writer,
                    depth,
                    key,
                    items[index] if index < len(items) else None,
                    metadata[index] if index < len(metadata) else None,
                )
        else:
            _write_element(writer, depth, key, item, extensions)


def _write_element(
    writer: _XmlWriter, depth: int, name: str, value: JsonValue, extensions: JsonValue
) -> None:
    if name == "div" and isinstance(value, str):
        namespace, local = _local(_parse(value.encode("utf-8")))
        if (namespace, local) != (XHTML_NAMESPACE, "div"):
            raise MarkupError("FHIR narrative div must be an XHTML <div> element")
        writer.raw(depth, value)
        return
    if isinstance(value, list):
        raise MarkupError(f"FHIR element {name!r} cannot nest arrays")
    if isinstance(value, dict):
        if "resourceType" in value:
            writer.open(depth, name, {})
            _write_resource(writer, depth + 1, value, root=False)
            writer.close(depth, name)
            return
        extension = name in ("extension", "modifierExtension")
        attributes = _attribute_members(value, in_resource=False, extension=extension)
        writer.open(depth, name, attributes)
        _write_members(writer, depth + 1, value, in_resource=False, extension=extension)
        writer.close(depth, name)
        return
    if value is None and extensions is None:
        return
    metadata = extensions if isinstance(extensions, dict) else {}
    attributes = _attribute_members(metadata, in_resource=False, extension=False)
    if value is not None:
        attributes["value"] = _scalar_text(value)
    nested = metadata.get("extension")
    if isinstance(nested, list) and nested:
        writer.open(depth, name, attributes)
        for item in nested:
            _write_element(writer, depth + 1, "extension", item, None)
        writer.close(depth, name)
    else:
        writer.empty(depth, name, attributes)


def load_fhir_xml(content: bytes) -> dict[str, JsonValue]:
    """Return FHIR JSON whose primitives are text and whose repetitions are not yet known."""
    return _read_resource(_parse(content))


def _read_resource(element: Element) -> dict[str, JsonValue]:
    namespace, resource_type = _local(element)
    if namespace != FHIR_NAMESPACE or not _RESOURCE_TYPE.fullmatch(resource_type):
        raise MarkupError(f"Not a FHIR resource element: {element.tag}")
    return {"resourceType": resource_type, **_read_members(element, in_resource=True)}


def _read_members(element: Element, *, in_resource: bool) -> dict[str, JsonValue]:
    members: dict[str, JsonValue] = {}
    if not in_resource and "id" in element.attrib:
        members["id"] = element.attrib["id"]
    if "url" in element.attrib:
        members["url"] = element.attrib["url"]
    values: dict[str, list[JsonValue]] = {}
    extensions: dict[str, list[JsonValue]] = {}
    for child in element:
        namespace, name = _local(child)
        if (namespace, name) == (XHTML_NAMESPACE, "div"):
            value, metadata = tostring(child, encoding="unicode"), None
        elif namespace != FHIR_NAMESPACE:
            raise MarkupError(
                f"Unexpected element outside the FHIR namespace: {child.tag}"
            )
        else:
            value, metadata = _read_element(child)
        values.setdefault(name, []).append(value)
        extensions.setdefault(name, []).append(metadata)
    for name, items in values.items():
        if name in members:
            raise MarkupError(f"FHIR element {name!r} conflicts with an attribute")
        members[name] = items[0] if len(items) == 1 else items
        metadata = extensions[name]
        if any(item is not None for item in metadata):
            members[f"_{name}"] = metadata[0] if len(metadata) == 1 else metadata
    return members


def _read_element(element: Element) -> tuple[JsonValue, JsonValue]:
    children = list(element)
    if len(children) == 1 and _RESOURCE_TYPE.fullmatch(_local(children[0])[1]):
        return _read_resource(children[0]), None
    if "value" not in element.attrib:
        return _read_members(element, in_resource=False), None
    metadata = _read_members(element, in_resource=False)
    unexpected = set(metadata) - {"id", "extension"}
    if unexpected:
        raise MarkupError(
            f"FHIR primitive {element.tag} has unexpected children: {sorted(unexpected)}"
        )
    if isinstance(metadata.get("extension"), dict):
        metadata["extension"] = [metadata["extension"]]
    return element.attrib["value"], metadata or None
