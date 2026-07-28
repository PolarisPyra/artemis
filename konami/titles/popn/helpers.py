"""Small equivalents of Asphyxia's ``$()`` and ``K.ITEM`` helpers."""

from __future__ import annotations

from typing import Any


def attr(node: Any, name: str, default: Any = None) -> Any:
    if not isinstance(node, dict):
        return default
    return node.get("@attr", {}).get(name, default)


def content(node: Any, default: Any = None) -> Any:
    if not isinstance(node, dict) or "@content" not in node:
        return default
    value = node["@content"]
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def child(node: Any, name: str, default: Any = None) -> Any:
    if not isinstance(node, dict):
        return default
    return node.get(name, default)


def item(type_name: str, value: Any, **extra: Any) -> dict:
    return {
        "@attr": {"__type": type_name, **extra},
        "@content": value if isinstance(value, (list, bytes, bytearray)) else [value],
    }


def array(type_name: str, value: list[Any], **extra: Any) -> dict:
    return {
        "@attr": {"__type": type_name, "__count": len(value), **extra},
        "@content": value,
    }


def scalar(value: Any, default: Any = 0) -> Any:
    try:
        if value is None:
            return default
        if isinstance(value, list):
            value = value[0] if value else default
        return int(value)
    except (TypeError, ValueError):
        return default


def walk_get(node: Any, path: str, default: Any = None) -> Any:
    current = node
    for part in path.split(".") if path else ():
        if isinstance(current, list):
            current = current[0] if current else None
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return default if current is None else current


def walk_set(node: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    current = node
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value
