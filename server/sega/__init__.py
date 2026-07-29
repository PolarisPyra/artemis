"""Lazy public exports for the SEGA server package.

Keeping these imports lazy prevents the Konami schema from importing the full
SEGA application while it is being initialized.
"""

from importlib import import_module

__all__ = ["ArtemisConfig", "MuchaServlet", "TitleServlet", "Utils"]

_EXPORTS = {
    "ArtemisConfig": ("server.sega.config", "ArtemisConfig"),
    "MuchaServlet": ("server.sega.mucha", "MuchaServlet"),
    "TitleServlet": ("server.sega.title", "TitleServlet"),
    "Utils": ("server.sega.utils", "Utils"),
}


def __getattr__(name: str):
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
