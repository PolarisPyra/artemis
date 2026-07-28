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

    async def dispatch(self, body: EamuseBody, info: EamuseInfo, response: EamuseResponse) -> None:
        handler = self._routes.get(info.game_code, {}).get(f"{body.module}.{body.method}")
        if handler is None:
            handler = self._fallback.get(info.game_code)
        if handler is not None:
            await handler(info, body.data.get("call", {}).get(body.module, {}), response)

