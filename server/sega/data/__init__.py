"""Lazy database exports.

The database module imports both SEGA and Konami metadata. Lazy exports keep
individual schema modules importable without creating a package cycle.
"""

from importlib import import_module

__all__ = ["Data", "cached"]

_EXPORTS = {
    "Data": ("server.sega.data.database", "Data"),
    "cached": ("server.sega.data.cache", "cached"),
}


def __getattr__(name: str):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
