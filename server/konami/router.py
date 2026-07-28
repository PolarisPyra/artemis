"""Generic e-amusement module/method router."""

from __future__ import annotations

from collections import defaultdict
from typing import Awaitable, Callable

from .protocol import EamuseBody, EamuseInfo, EamuseResponse

Handler = Callable[[EamuseInfo, dict, "EamuseResponse"], Awaitable[object | None]]


class EamuseRouter:
    def __init__(self) -> None:
        self._routes: dict[str, dict[str, Handler]] = defaultdict(dict)
        self._fallback: dict[str, Handler] = {}
        self._webui: dict[str, Callable[[str, dict], Awaitable[None]]] = {}

    def add(self, game_code: str, module: str, method: str, handler: Handler) -> None:
        route = f"{module}.{method}"
        self._routes[game_code][route] = handler

    def fallback(self, game_code: str, handler: Handler) -> None:
        self._fallback[game_code] = handler

    def webui(self, game_code: str, handler: Callable[[str, dict], Awaitable[None]]):
        self._webui[game_code] = handler

    def dispatch_webui(self, game_code: str, name: str, data: dict):
        handler = self._webui.get(game_code)
        if handler is None:
            return None
        return handler(name, data)

    async def dispatch(
        self, body: EamuseBody, info: EamuseInfo, response: EamuseResponse
    ) -> None:
        handler = self._routes.get(info.game_code, {}).get(
            f"{body.module}.{body.method}"
        )
        if handler is None:
            handler = self._fallback.get(info.game_code)
        if handler is not None:
            module_data = body.data.get("call", {}).get(body.module, {})
            # K-bin represents repeated top-level nodes as arrays.  The title
            # Handlers consume the object convention used by the title routes,
            # so a single repeated module is unwrapped here.
            if isinstance(module_data, list) and len(module_data) == 1:
                module_data = module_data[0]
            await handler(
                info, module_data if isinstance(module_data, dict) else {}, response
            )
