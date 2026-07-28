"""Conversion between e-amusement XML and Asphyxia's object representation."""

from __future__ import annotations

from collections import OrderedDict
import re
from xml.etree import ElementTree
from xml.sax.saxutils import escape as escape_xml, quoteattr


def _add(parent: dict, name: str, value: object) -> None:
    if name not in parent:
        parent[name] = value
    elif isinstance(parent[name], list):
        parent[name].append(value)
    else:
        parent[name] = [parent[name], value]


def _element_to_data(element: ElementTree.Element) -> dict:
    value: dict = OrderedDict()
    if element.attrib:
        value["@attr"] = dict(element.attrib)
    children = list(element)
    if children:
        for child in children:
            _add(value, child.tag, _element_to_data(child))
        text = (element.text or "").strip()
        if text:
            value["@content"] = text
    else:
        text = element.text or ""
        if text:
            value["@content"] = text
    _decode_typed_content(value)
    return value


def _decode_typed_content(value: dict) -> None:
    attrs = value.get("@attr", {})
    content = value.get("@content")
    if not isinstance(content, str):
        return
    type_name = attrs.get("__type")
    if type_name == "bin":
        try:
            value["@content"] = bytes.fromhex("".join(content.split()))
        except ValueError:
            pass
    elif type_name == "ip4":
        converted = []
        for item in content.split():
            try:
                parts = [int(part) for part in item.split(".")]
                if len(parts) != 4 or any(part < 0 or part > 255 for part in parts):
                    raise ValueError
                number = 0
                for part in parts:
                    number = (number << 8) | part
                converted.append(number)
            except ValueError:
                return
        value["@content"] = converted


def detect_xml_encoding(raw: bytes) -> str:
    declaration = re.match(rb"\s*<\?xml[^>]+encoding=['\"]([^'\"]+)", raw[:256], re.I)
    if declaration is None:
        return "utf-8"
    value = declaration.group(1).decode("ascii", errors="ignore").lower()
    return {
        "utf8": "utf-8",
        "utf-8": "utf-8",
        "shift_jis": "shift_jis",
        "shift-jis": "shift_jis",
        "euc-jp": "euc_jp",
    }.get(value, value)


def xml_to_data(raw: bytes, encoding: str | None = None) -> dict:
    encoding = encoding or detect_xml_encoding(raw)
    root = ElementTree.fromstring(raw.decode(encoding, errors="replace"))
    return {root.tag: _element_to_data(root)}


def _escape(value: object) -> str:
    return escape_xml(str(value))


def _render(name: str, value: object) -> str:
    if isinstance(value, list):
        return "".join(_render(name, item) for item in value)
    if not isinstance(value, dict):
        return f"<{name}>{_escape(value)}</{name}>"
    attrs = value.get("@attr", {})
    attr_text = "".join(
        f" {key}={quoteattr(str(val))}"
        for key, val in attrs.items()
    )
    raw_content = value.get("@content", "")
    if attrs.get("__type") == "bin" and isinstance(raw_content, (bytes, bytearray)):
        raw_content = bytes(raw_content).hex()
    if isinstance(raw_content, list):
        if attrs.get("__type") == "ip4":
            raw_content = " ".join(_int_to_ip(item) for item in raw_content)
        else:
            raw_content = " ".join(str(item) for item in raw_content)
    content = _escape(raw_content) if "@content" in value else ""
    children = "".join(
        _render(key, child) for key, child in value.items() if not key.startswith("@")
    )
    if not content and not children:
        return f"<{name}{attr_text}/>"
    return f"<{name}{attr_text}>{content}{children}</{name}>"


def _int_to_ip(value: object) -> str:
    try:
        number = int(value)
        return ".".join(str((number >> shift) & 0xFF) for shift in (24, 16, 8, 0))
    except (TypeError, ValueError):
        return "0.0.0.0"


def data_to_xml(data: dict, encoding: str = "utf-8") -> bytes:
    root = "".join(_render(key, value) for key, value in data.items())
    declaration = f"<?xml version='1.0' encoding='{encoding.upper()}'?>\n"
    return (declaration + root).encode(encoding, errors="replace")
