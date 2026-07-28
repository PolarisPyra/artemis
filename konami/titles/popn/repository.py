"""Pop'n persistence and score conversion helpers."""

from __future__ import annotations

from copy import deepcopy

from core.data import Data


class PopnRepository:
    def __init__(self, data: Data, game_code: str) -> None:
        self.data = data
        # Asphyxia's Pop'n DB collections are keyed by refid and collection;
        # game versions are carried by the document's version field.  M39 is
        # the shared namespace used by the modern Pop'n route family.
        self.game_code = "M39"

    async def profile(self, refid: str) -> dict:
        return await self.data.konami.get_document(
            refid, self.game_code, "profile"
        ) or {
            "collection": "profile",
            "name": "ゲスト",
            "friendId": "000000000000",
            "dataVersion": 2,
        }

    async def save_profile(self, refid: str, profile: dict) -> None:
        await self.data.konami.put_document(refid, self.game_code, "profile", profile)

    async def params(self, refid: str, version: str) -> dict:
        return await self.data.konami.get_document(
            refid, self.game_code, "params", version
        ) or {
            "collection": "params",
            "version": version,
            "params": {},
        }

    async def save_params(self, refid: str, version: str, params: dict) -> None:
        await self.data.konami.put_document(
            refid, self.game_code, "params", params, version
        )

    async def scores(self, refid: str, version: str, force_version: bool = False) -> dict:
        if not force_version and getattr(
            self.data.config.konami, "enable_score_sharing", True
        ):
            merged = {"collection": "scores", "version": version, "scores": {}}
            for _, document in await self.data.konami.documents(
                self.game_code, "scores"
            ):
                for key, score in document.get("scores", {}).items():
                    current = merged["scores"].get(key)
                    if current is None:
                        merged["scores"][key] = deepcopy(score)
                    else:
                        current["score"] = max(
                            current.get("score", 0), score.get("score", 0)
                        )
                        current["cnt"] = current.get("cnt", 0) + score.get("cnt", 0)
                        current["clear_type"] = max(
                            current.get("clear_type", 0), score.get("clear_type", 0)
                        )
            return merged
        return await self.data.konami.get_document(
            refid, self.game_code, "scores", version
        ) or {
            "collection": "scores",
            "version": version,
            "scores": {},
        }

    async def save_scores(self, refid: str, version: str, scores: dict) -> None:
        await self.data.konami.put_document(
            refid, self.game_code, "scores", scores, version
        )

    async def achievements(self, refid: str, version: str, default: dict) -> dict:
        return await self.data.konami.get_document(
            refid, self.game_code, "achievements", version
        ) or deepcopy(default)

    async def save_achievements(
        self, refid: str, version: str, achievements: dict
    ) -> None:
        await self.data.konami.put_document(
            refid, self.game_code, "achievements", achievements, version
        )

    async def rivals(self, refid: str) -> dict:
        return await self.data.konami.get_document(refid, self.game_code, "rivals") or {
            "collection": "rivals",
            "rivals": [],
        }

    async def documents(
        self, collection: str, version: str = ""
    ) -> list[tuple[str, dict]]:
        return await self.data.konami.documents(self.game_code, collection, version)
