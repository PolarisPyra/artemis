"""Generic Konami module/method router and plugin contract."""

from __future__ import annotations

from collections import defaultdict
from typing import Awaitable, Callable

from .protocol import EamuseBody, EamuseInfo, EamuseResponse

Handler = Callable[[EamuseInfo, dict, "EamuseResponse"], Awaitable[object | None]]


class KonamiPlugin:
    game_codes: tuple[str, ...] = ()

    def register(self, router: "EamuseRouter") -> None:
        raise NotImplementedError


class EamuseRouter:
    def __init__(self) -> None:
        self._routes: dict[str, dict[str, Handler]] = defaultdict(dict)
        self._fallback: dict[str, Handler] = {}
        self._owners: dict[tuple[str, str], str] = {}
        self._fallback_owners: dict[str, str] = {}
        self._registering_plugin = ""

    def register_plugin(self, plugin: KonamiPlugin) -> None:
        self._registering_plugin = getattr(
            plugin, "identifier", plugin.__class__.__name__
        )
        try:
            plugin.register(self)
        finally:
            self._registering_plugin = ""

    def add(self, game_code: str, module: str, method: str, handler: Handler) -> None:
        route = f"{module}.{method}"
        self._routes[game_code][route] = handler
        if self._registering_plugin:
            self._owners[(game_code, route)] = self._registering_plugin

    def fallback(self, game_code: str, handler: Handler) -> None:
        self._fallback[game_code] = handler
        if self._registering_plugin:
            self._fallback_owners[game_code] = self._registering_plugin

    async def dispatch(
        self, body: EamuseBody, info: EamuseInfo, response: EamuseResponse
    ) -> None:
        handler = self._routes.get(info.game_code, {}).get(
            f"{body.module}.{body.method}"
        )
        if handler is None:
            handler = self._fallback.get(info.game_code)
        if handler is not None:
            response.plugin = self._owners.get(
                (info.game_code, f"{body.module}.{body.method}"),
                self._fallback_owners.get(info.game_code),
            )
            module_data = body.data.get("call", {}).get(body.module, {})
            # K-bin represents repeated top-level nodes as arrays.  The title
            # handlers consume the object convention used by Asphyxia, so a
            # single repeated module is unwrapped here.
            if isinstance(module_data, list) and len(module_data) == 1:
                module_data = module_data[0]
            await handler(
                info, module_data if isinstance(module_data, dict) else {}, response
            )
