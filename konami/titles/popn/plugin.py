"""Pop'n Music e-amusement title adapter.

The version-specific handlers are deliberately isolated behind this plugin so
the common Konami transport can support other games without title branching.
"""

from __future__ import annotations

import secrets
from typing import Any

from core.config import CoreConfig
from core.data import Data
from core.konami.protocol import EamuseInfo, EamuseResponse
from core.konami.router import EamuseRouter, KonamiPlugin


def attrs(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("@attr", {}) if isinstance(data, dict) else {}


class PopnPlugin(KonamiPlugin):
    game_codes = ("K39", "L39", "M39")

    def __init__(self, cfg: CoreConfig) -> None:
        self.cfg = cfg
        self.data = Data(cfg)

    def register(self, router: EamuseRouter) -> None:
        for code in self.game_codes:
            router.add(code, "game", "get", self.game_get)
            router.add(code, "playerdata", "new", self.player_new)
            router.add(code, "playerdata", "conversion", self.player_new)
            router.add(code, "playerdata", "get", self.player_get)
            router.add(code, "playerdata", "set", self.player_set)
            router.add(code, "playerdata", "friend", self.player_friend)
            router.fallback(code, self.unhandled)

    async def game_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        version = {"K39": "19", "L39": "20", "M39": "21"}.get(info.game_code, "19")
        response.content = {"@attr": {"game_phase": "1", "version": version}}

    async def player_new(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        refid = attrs(data).get("refid", attrs(data).get("dataid", ""))
        if not refid:
            refid = secrets.token_hex(8).upper()
        profile = await self.data.konami.get_document(refid, info.game_code, "profile") or {
            "collection": "profile", "name": "ゲスト", "friendId": f"{secrets.randbelow(10**12):012d}", "dataVersion": 2,
        }
        await self.data.konami.put_document(refid, info.game_code, "profile", profile)
        response.content = {"@attr": {"dataid": refid, "refid": refid}, "player": profile}

    async def player_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        refid = attrs(data).get("refid", attrs(data).get("dataid", ""))
        profile = await self.data.konami.get_document(refid, info.game_code, "profile") or {
            "collection": "profile", "name": "ゲスト", "friendId": "000000000000", "dataVersion": 2,
        }
        response.content = {"@attr": {"dataid": refid, "refid": refid}, "player": profile}

    async def player_set(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        refid = attrs(data).get("refid", attrs(data).get("dataid", ""))
        profile = dict(data.get("player", {}))
        await self.data.konami.put_document(refid, info.game_code, "profile", profile)
        response.content = {"@attr": {"dataid": refid, "refid": refid}}

    async def player_friend(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"@attr": {"friend_num": "0"}}

    async def unhandled(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.status = 0
