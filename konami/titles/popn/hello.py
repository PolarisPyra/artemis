"""Hello! Pop'n Music (JMP) routes from the Asphyxia plugin."""

from __future__ import annotations

from core.data import Data
from core.konami.protocol import EamuseInfo, EamuseResponse

from .helpers import attr, child, item, scalar


class PopnHelloHandler:
    def __init__(self, data: Data) -> None:
        self.data = data
        self.game_code = "M39"

    async def profile(self, refid: str) -> dict:
        return await self.data.konami.get_document(
            refid, self.game_code, "profile"
        ) or {
            "collection": "profile",
            "unlockAll": False,
            "history": {"chara": 0, "level": 0, "mid": 0, "style": 0},
            "charas": {},
        }

    async def save_profile(self, refid: str, profile: dict) -> None:
        await self.data.konami.put_document(
            refid, self.game_code, "profile", profile
        )

    async def scores(self, refid: str) -> dict:
        return await self.data.konami.get_document(
            refid, self.game_code, "scores"
        ) or {"collection": "scores", "scores": {}}

    async def save_scores(self, refid: str, scores: dict) -> None:
        await self.data.konami.put_document(
            refid, self.game_code, "scores", scores
        )

    async def common(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "flag": {"@attr": {"id": "1", "s1": "1", "s2": "1", "t": "1"}},
            "cnt_music": item("u32", 36),
        }

    async def shop(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.status = 0

    async def new(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        await self.save_profile(refid, await self.profile(refid))

    async def load(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        profile = await self.profile(refid)
        if profile.get("unlockAll", False):
            chara = [
                {"@attr": {"id": str(index), "love": "5"}}
                for index in range(11)
            ]
        else:
            chara = [
                {"@attr": {"id": str(index), "love": str(love)}}
                for index, love in profile.get("charas", {}).items()
            ]
        history = profile.get("history", {})
        response.content = {
            "last": {
                "@attr": {
                    "chara": str(history.get("chara", 0)),
                    "level": str(history.get("level", 0)),
                    "music_id": str(history.get("mid", 0)),
                    "style": str(history.get("style", 0)),
                }
            },
            "chara": chara,
        }

    async def load_m(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        scores = (await self.scores(refid)).get("scores", {})
        music = []
        for music_id, styles in scores.items():
            style_nodes = []
            for style_id, levels in styles.items():
                style_nodes.append(
                    {
                        "@attr": {"id": str(style_id)},
                        "level": [
                            {
                                "@attr": {
                                    "id": str(level_id),
                                    "score": str(score.get("score", 0)),
                                    "clear_type": str(score.get("clear", 0)),
                                }
                            }
                            for level_id, score in levels.items()
                        ],
                    }
                )
            music.append(
                {"@attr": {"music_id": str(music_id)}, "style": style_nodes}
            )
        response.content = {"music": music}

    async def save_m(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        clear = scalar(attr(data, "clear_type", -1), -1)
        level = scalar(attr(data, "level", -1), -1)
        music_id = scalar(attr(data, "music_id", -1), -1)
        score = scalar(attr(data, "score", -1), -1)
        style = scalar(attr(data, "style", -1), -1)
        if min(clear, level, music_id, score, style) < 0:
            return
        scores = await self.scores(refid)
        music = scores.setdefault("scores", {}).setdefault(str(music_id), {})
        style_scores = music.setdefault(str(style), {})
        previous = style_scores.get(str(level), {})
        style_scores[str(level)] = {
            "score": max(previous.get("score", 0), score),
            "clear": max(previous.get("clear", 0), clear),
        }
        await self.save_scores(refid, scores)

    async def save(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        last = child(data, "last", {})
        chara = scalar(attr(last, "chara", -1), -1)
        level = scalar(attr(last, "level", -1), -1)
        love = scalar(attr(last, "love", -1), -1)
        music_id = scalar(attr(last, "music_id", -1), -1)
        style = scalar(attr(last, "style", -1), -1)
        if min(chara, level, love, music_id, style) < 0:
            return
        profile = await self.profile(refid)
        if not profile.get("unlockAll", False):
            charas = profile.setdefault("charas", {})
            charas[str(chara)] = scalar(charas.get(str(chara), 0)) + love
        profile["history"] = {
            "chara": chara,
            "mid": music_id,
            "level": level,
            "style": style,
        }
        await self.save_profile(refid, profile)

    async def set_unlock_state(self, data: dict) -> None:
        refid = str(data.get("refid", ""))
        if not refid:
            return
        profile = await self.profile(refid)
        profile["unlockAll"] = data.get("unlock_all") == "on"
        await self.save_profile(refid, profile)
