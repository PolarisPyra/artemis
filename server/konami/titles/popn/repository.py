"""Pop'n persistence and score conversion helpers."""

from __future__ import annotations

from copy import deepcopy

from server.sega.data import Data


class PopnRepository:
    def __init__(self, data: Data, game_code: str) -> None:
        self.data = data
        # M39 is the shared modern Pop'n profile namespace. The requested
        # game code is retained for legacy document compatibility.
        self.game_code = game_code
        self.profile_code = "M39"

    async def profile(self, refid: str) -> dict:
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            profile = await self.data.konami.get_document(
                refid, self.profile_code, "profile"
            )
            if profile is not None:
                await self.data.konami.put_profile(refid, profile)
        return profile or {
            "collection": "profile",
            "name": "ゲスト",
            "friendId": "000000000000",
            "dataVersion": 2,
        }

    async def save_profile(self, refid: str, profile: dict) -> None:
        await self.data.konami.put_profile(refid, profile)

    async def update_profile_name(self, refid: str, name: str) -> None:
        profile = await self.profile(refid)
        if profile is not None:
            profile["name"] = name
            await self.save_profile(refid, profile)

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
        versions = [version] if force_version else [f"v{i}" for i in range(19, 28)]
        merged = {"collection": "scores", "version": version, "scores": {}}
        for selected_version in versions:
            document = await self.data.konami.get_scores(refid, selected_version)
            if not document["scores"]:
                legacy = await self.data.konami.get_document(
                    refid, self.game_code, "scores", selected_version
                )
                if legacy is not None:
                    document = legacy
                    await self.data.konami.put_scores(refid, selected_version, legacy)
            for key, score in document.get("scores", {}).items():
                current = merged["scores"].get(key)
                if current is None:
                    merged["scores"][key] = deepcopy(score)
                else:
                    current["score"] = max(current.get("score", 0), score.get("score", 0))
                    current["cnt"] = current.get("cnt", 0) + score.get("cnt", 0)
                    current["clear_type"] = max(
                        current.get("clear_type", 0), score.get("clear_type", 0)
                    )
        return merged

    async def save_scores(self, refid: str, version: str, scores: dict) -> None:
        await self.data.konami.put_scores(refid, version, scores)

    async def achievements(self, refid: str, version: str, default: dict) -> dict:
        achievements = await self.data.konami.get_achievement_document(
            refid, self.profile_code, version
        )
        if achievements is None:
            achievements = await self.data.konami.get_document(
                refid, self.game_code, "achievements", version
            )
            if achievements is not None:
                await self.data.konami.put_achievement_document(
                    refid, self.profile_code, version, achievements
                )
        return achievements or deepcopy(default)

    async def save_achievements(
        self, refid: str, version: str, achievements: dict
    ) -> None:
        await self.data.konami.put_achievement_document(
            refid, self.profile_code, version, achievements
        )

    async def rivals(self, refid: str) -> dict:
        rival_ids = await self.data.konami.get_rivals(refid)
        if not rival_ids:
            legacy = await self.data.konami.get_document(
                refid, self.game_code, "rivals"
            )
            if legacy is not None:
                rival_ids = list(legacy.get("rivals", []))
                await self.data.konami.put_rivals(refid, rival_ids)
        return {"collection": "rivals", "rivals": rival_ids}

    async def add_rival(self, refid: str, rivalid: str) -> bool:
        refid = refid.strip()
        rivalid = str(rivalid)
        if not refid or not rivalid:
            return False
        rival_profile = await self.data.konami.get_document(
            rivalid, self.game_code, "profile"
        )
        if rival_profile is None:
            return False
        rivals = await self.rivals(refid)
        if len(rivals.get("rivals", [])) >= 4:
            return False
        rivals.setdefault("rivals", []).append(rivalid)
        await self.data.konami.put_rivals(refid, rivals["rivals"])
        return True

    async def delete_rival(self, refid: str, rivalid: str) -> bool:
        rivals = await self.rivals(refid)
        rival_list = rivals.setdefault("rivals", [])
        if rivalid not in rival_list:
            return False
        rival_list.remove(rivalid)
        await self.data.konami.put_rivals(refid, rival_list)
        return True

    async def documents(
        self, collection: str, version: str = ""
    ) -> list[tuple[str, dict]]:
        return await self.data.konami.documents(self.profile_code, collection, version)
