"""MÚSECA route registration for Artemis."""

from __future__ import annotations

import hashlib

from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn import attr, content, item, scalar


class MusecaRoutes:
    """MÚSECA 1/1+1/2 routes, matching bemaniutils' PIX backend."""

    game_codes = ("PIX",)

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.data = Data(cfg)

    def service_modules(self, game_code: str, model: str = "") -> tuple[str, ...]:
        return ("game_3", "eventlog")

    def register(self, router: EamuseRouter) -> None:
        routes = (
            ("common", self.pix_common),
            ("hiscore", self.pix_hiscore),
            ("shop", self.pix_shop),
            ("exception", self.pix_frozen),
            ("new", self.pix_new),
            ("frozen", self.pix_frozen),
            ("load", self.pix_load),
            ("save", self.pix_save),
            ("play_e", self.pix_play_e),
            ("load_m", self.pix_load_m),
            ("save_m", self.pix_save_m),
        )
        for method, handler in routes:
            router.add("PIX", "game_3", method, handler)

    async def pix_common(self, info, data, response):
        response.content = {
            "music_limited": {"info": []},
            "event": {"info": [
                {"event_id": item("u32", event_id)}
                for event_id in (1, 83, 130, 194, 195, 98, 145, 146, 147, 148, 149, 56, 86, 105, 140, 211, 143)
            ]},
        }

    async def pix_shop(self, info, data, response):
        response.content = {"nxt_time": item("u32", 300)}

    async def pix_frozen(self, info, data, response):
        response.content = {"result": item("u8", 0)}

    async def pix_hiscore(self, info, data, response):
        response.content = {
            "hitchart": {"info": []},
            "hiscore_allover": {"info": []},
            "hiscore_location": {"info": []},
            "clear_rate": {"d": []},
        }

    async def pix_play_e(self, info, data, response):
        response.content = {}

    async def pix_new(self, info, data, response):
        refid = content(data.get("refid")) or attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        if await self.data.konami.get_profile(refid) is None:
            await self.data.konami.put_profile(
                refid,
                {"collection": "profile", "code": self._id(refid), "name": content(data.get("name")) or "NONAME",
                 "play_count": 0, "item": {}, "hidden_param": [0] * 20},
            )
        await self.data.konami.put_document(refid, "PIX", "scores", {"collection": "scores", "scores": {}})
        response.content = {"result": item("u8", 0)}

    async def pix_load(self, info, data, response):
        refid = content(data.get("refid")) or attr(data, "refid", "")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.content = {"result": item("u8", 1)}
            return
        response.content = {
            "hidden_param": item("s32", profile.get("hidden_param", [0] * 20)),
            "play_count": item("u32", profile.get("play_count", 0)),
            "name": item("str", profile.get("name", "NONAME")),
            "code": item("str", str(profile.get("code", self._id(refid)))),
            "item": {"info": []},
            "result": item("u8", 0),
            "ea_shop": {"packet_booster": item("s32", 0), "block_booster": item("s32", 0)},
        }

    async def pix_save(self, info, data, response):
        refid = content(data.get("refid")) or attr(data, "refid", "")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        for name in ("hidden_param", "play_count", "blaster_count", "music_id", "music_type"):
            if name in data:
                profile[name] = content(data[name], data[name])
        await self.data.konami.put_profile(refid, profile)

    async def pix_load_m(self, info, data, response):
        refid = content(data.get("dataid")) or attr(data, "dataid", "") or content(data.get("refid"))
        document = await self.data.konami.get_document(refid, "PIX", "scores") or {"scores": {}}
        music = []
        for song_id, styles in document.get("scores", {}).items():
            for music_type, score in (styles.items() if isinstance(styles, dict) else ()):
                music.append({"music_id": item("u32", scalar(song_id)), "music_type": item("u32", scalar(music_type)),
                              "score": item("u32", scalar(score.get("score"))), "cnt": item("u32", scalar(score.get("count"))),
                              "clear_type": item("u32", scalar(score.get("clear_type"))), "score_grade": item("u32", scalar(score.get("score_grade"))),
                              "btn_rate": item("u32", scalar(score.get("btn_rate"))), "long_rate": item("u32", scalar(score.get("long_rate"))),
                              "vol_rate": item("u32", scalar(score.get("vol_rate")))})
        response.content = {"new": {"music": music}, "old": {}}

    async def pix_save_m(self, info, data, response):
        refid = content(data.get("refid")) or attr(data, "refid", "")
        if not refid:
            response.status = 1
            return
        document = await self.data.konami.get_document(refid, "PIX", "scores") or {"collection": "scores", "scores": {}}
        song_id = scalar(content(data.get("music_id")), scalar(attr(data, "music_id"), 0))
        music_type = scalar(content(data.get("music_type")), scalar(attr(data, "music_type"), 0))
        scores = document.setdefault("scores", {})
        current = scores.setdefault(str(song_id), {}).setdefault(str(music_type), {})
        for name in ("score", "count", "clear_type", "score_grade", "btn_rate", "long_rate", "vol_rate"):
            value = scalar(content(data.get(name)), scalar(attr(data, name), 0))
            if value:
                current[name] = value
        await self.data.konami.put_document(refid, "PIX", "scores", document)
        response.content = {"result": item("s32", 0)}

    @staticmethod
    def _id(refid: str) -> int:
        return int(hashlib.sha256(f"pix:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000
