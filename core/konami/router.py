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

    def add(self, game_code: str, module: str, method: str, handler: Handler) -> None:
        self._routes[game_code][f"{module}.{method}"] = handler

    def fallback(self, game_code: str, handler: Handler) -> None:
        self._fallback[game_code] = handler

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
            # handlers consume the object convention used by Asphyxia, so a
            # single repeated module is unwrapped here.
            if isinstance(module_data, list) and len(module_data) == 1:
                module_data = module_data[0]
            await handler(
                info, module_data if isinstance(module_data, dict) else {}, response
            )
