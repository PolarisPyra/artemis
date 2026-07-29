"""Route contracts for the smaller Konami title families."""

from __future__ import annotations

from typing import ClassVar

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn_support.helpers import array, attr, content, item, scalar


class LegacyTitleRoutes:
    """Register explicit route surfaces whose title payloads are versioned."""

    title_routes: ClassVar[dict[str, tuple[tuple[str, str], ...]]] = {
        "NBT": (
            ("info2", "common"),
            ("pcb2", "boot"),
            ("player2", "start"),
            ("player2", "continue"),
            ("player2", "succeed"),
            ("player2", "read"),
            ("player2", "write"),
            ("player2", "stagedata_write"),
            ("player2", "course_stage_data_write"),
            ("player2", "course_data_write"),
        ),
        "PIX": (
            ("game_3", "common"),
            ("game_3", "shop"),
            ("game_3", "exception"),
            ("game_3", "hiscore"),
            ("game_3", "lounge"),
            ("game_3", "frozen"),
            ("game_3", "play_e"),
            ("game_3", "new"),
            ("game_3", "save"),
            ("game_3", "save_m"),
            ("game_3", "load"),
            ("game_3", "load_m"),
        ),
        "PAN": (
            ("common", "get_common_info"),
            ("common", "get_music_info"),
            ("player", "get_musicdata"),
            ("player", "get_playdata"),
            ("player", "regist_playdata"),
            ("player", "set_total_result"),
            ("player", "set_stage_result"),
            ("op2_common", "get_common_info"),
            ("op2_common", "get_music_info"),
            ("op2_player", "get_musicdata"),
            ("op2_player", "get_playdata"),
            ("op2_player", "regist_playdata"),
            ("op2_player", "set_total_result"),
            ("op2_player", "set_stage_result"),
        ),
    }
    popn_legacy_codes: ClassVar[tuple[str, ...]] = ("G15", "H16", "I17", "J39")
    popn_legacy_routes: ClassVar[tuple[tuple[str, str], ...]] = (
        ("game", "get"),
        ("playerdata", "new"),
        ("playerdata", "conversion"),
        ("playerdata", "get"),
        ("playerdata", "set"),
        ("playerdata", "friend"),
        ("playerdata", "town"),
    )

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.cfg = cfg
        self.data = Data(cfg)

    @property
    def game_codes(self) -> tuple[str, ...]:
        return tuple(self.title_routes) + self.popn_legacy_codes

    def service_modules(self, game_code: str, model: str = "") -> tuple[str, ...]:
        if game_code in self.popn_legacy_codes:
            return ("game", "playerdata")
        return tuple(dict.fromkeys(module for module, _ in self.title_routes[game_code]))

    def register(self, router: EamuseRouter) -> None:
        pix_handlers = {
            ("game_3", "common"): self.pix_common,
            ("game_3", "shop"): self.pix_shop,
            ("game_3", "frozen"): self.pix_frozen,
            ("game_3", "lounge"): self.pix_lounge,
            ("game_3", "new"): self.pix_new,
            ("game_3", "load"): self.pix_load,
            ("game_3", "save"): self.pix_save,
            ("game_3", "load_m"): self.pix_load_m,
            ("game_3", "save_m"): self.pix_save_m,
        }
        bst_handlers = {
            ("info2", "common"): self.bst_common,
            ("pcb2", "boot"): self.bst_boot,
            ("player2", "start"): self.bst_start,
            ("player2", "continue"): self.bst_start,
            ("player2", "succeed"): self.bst_succeed,
        }
        nostalgia_handlers = {
            ("common", "get_common_info"): self.nostalgia_common,
            ("op2_common", "get_common_info"): self.nostalgia_common,
        }
        for game_code, routes in self.title_routes.items():
            for module, method in routes:
                handler = pix_handlers.get((module, method), bst_handlers.get((module, method), nostalgia_handlers.get((module, method), self.handle)))
                router.add(game_code, module, method, handler)
        for game_code in self.popn_legacy_codes:
            for module, method in self.popn_legacy_routes:
                router.add(game_code, module, method, self.handle)

    async def bst_common(self, info, data, response):
        response.content = {"event_ctrl": {"data": []}}

    async def bst_boot(self, info, data, response):
        response.content = {
            "sinfo": {"nm": item("str", "Artemis"), "cl_enbl": item("bool", 1),
                      "cl_h": item("u8", 0), "cl_m": item("u8", 0)}
        }

    async def bst_start(self, info, data, response):
        response.content = {"player_id": item("s32", -1), "start_time": item("u64", 0)}

    async def bst_succeed(self, info, data, response):
        response.content = {"play": item("bool", 0), "data": {"name": item("str", "")},
                            "record": {}, "hacker": {}, "phantom": {}}

    async def nostalgia_common(self, info, data, response):
        response.content = {
            "permitted_list": {"flag": [array("s32", [-1] * 32, sheet_type=str(index)) for index in range(4)]},
            "olupdate": {"delete_flag": item("bool", 0)},
        }

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

    async def pix_lounge(self, info, data, response):
        response.content = {"interval": item("u32", 10)}

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
        for source, target in (("score", "score"), ("clear_type", "clear_type"), ("score_grade", "score_grade"), ("btn_rate", "btn_rate"), ("long_rate", "long_rate"), ("vol_rate", "vol_rate")):
            value = scalar(content(data.get(source)), scalar(attr(data, source), 0))
            current[target] = max(scalar(current.get(target), 0), value)
        current["count"] = scalar(current.get("count"), 0) + 1
        await self.data.konami.put_document(refid, "PIX", "scores", document)
    async def handle(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        if info.module in {"info2", "pcb2", "common", "op2_common", "game_3"}:
            response.content = {"result": item("s32", 0)}
        response.status = 0

    @staticmethod
    def _id(refid: str) -> int:
        import hashlib

        return int(hashlib.sha256(f"pix:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000
