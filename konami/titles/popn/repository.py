"""Pop'n persistence and score conversion helpers."""

from __future__ import annotations

from copy import deepcopy

from core.data import Data


class PopnRepository:
    def __init__(self, data: Data, game_code: str) -> None:
        self.data = data
        self.game_code = game_code

    async def profile(self, refid: str) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "profile") or {
            "collection": "profile", "name": "ゲスト", "friendId": "000000000000", "dataVersion": 2,
        }

    async def save_profile(self, refid: str, profile: dict) -> None:
        await self.data.konami.put_document(refid, self.game_code, "profile", profile)

    async def params(self, refid: str, version: str) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "params", version) or {
            "collection": "params", "version": version, "params": {},
        }

    async def save_params(self, refid: str, version: str, params: dict) -> None:
        await self.data.konami.put_document(refid, self.game_code, "params", params, version)

    async def scores(self, refid: str, version: str) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "scores", version) or {
            "collection": "scores", "version": version, "scores": {},
        }

    async def save_scores(self, refid: str, version: str, scores: dict) -> None:
        await self.data.konami.put_document(refid, self.game_code, "scores", scores, version)

    async def achievements(self, refid: str, version: str, default: dict) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "achievements", version) or deepcopy(default)

    async def save_achievements(self, refid: str, version: str, achievements: dict) -> None:
        await self.data.konami.put_document(refid, self.game_code, "achievements", achievements, version)

    async def rivals(self, refid: str) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "rivals") or {"collection": "rivals", "rivals": []}

