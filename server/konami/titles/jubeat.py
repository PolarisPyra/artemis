"""Native jubeat L44 e-amusement handlers."""

from __future__ import annotations

import hashlib
from typing import ClassVar

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn_support.helpers import array, attr, content, item


class JubeatRoutes:
    """Port the jubeat plugin's gametop/gameend route contract."""

    game_codes: ClassVar[tuple[str, ...]] = ("H44", "J44", "L44")

    @classmethod
    def service_modules(cls, game_code: str, model: str = "") -> tuple[str, ...]:
        return ("gametop", "gameend", "shopinfo", "lobby", "netlog", "logger")

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.data = Data(cfg)

    def register(self, router: EamuseRouter) -> None:
        routes = {
            "gametop": {
                "regist": self.gametop_regist,
                "get_info": self.gametop_get_info,
                "get_pdata": self.gametop_regist,
                "get_mdata": self.gametop_get_mdata,
                "get_meeting": self.gametop_get_meeting,
            },
            "gameend": {"final": self.success, "regist": self.gameend_regist},
            "shopinfo": {"regist": self.shopinfo_regist},
            "lobby": {
                "check": self.success,
                "entry": self.success,
                "refresh": self.success,
                "report": self.success,
            },
            "netlog": {"send": self.success},
            "logger": {"report": self.success},
        }
        for code in self.game_codes:
            for module, methods in routes.items():
                for method, handler in methods.items():
                    router.add(code, module, method, handler)

    async def gametop_regist(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        player = payload.get("player", {})
        refid = attr(player, "refid") or content(player.get("refid"))
        name = attr(player, "name") or content(player.get("name")) or "PLAYER"
        if not refid:
            response.status = 1
            return
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            profile = {
                "collection": "profile",
                "jubeatId": self._id(refid),
                "eventFlag": 0,
                "name": str(name),
                "isFirstplay": True,
                "lastShopname": "",
                "lastAreaname": "",
            }
            await self.data.konami.put_profile(refid, profile)
        response.compress = True
        response.content = {
            "data": {
                "player": {
                    "jid": item("s32", profile["jubeatId"]),
                    "session_id": item("s32", 1),
                    "name": item("str", profile.get("name", "PLAYER")),
                    "event_flag": item("u64", profile.get("eventFlag", 0)),
                    "info": {
                        "tune_cnt": item("s32", profile.get("tuneCount", 0)),
                        "save_cnt": item("s32", profile.get("saveCount", 0)),
                        "saved_cnt": item("s32", profile.get("savedCount", 0)),
                        "clear_cnt": item("s32", profile.get("clearCount", 0)),
                        "fc_cnt": item("s32", profile.get("fcCount", 0)),
                        "ex_cnt": item("s32", profile.get("exCount", 0)),
                        "match_cnt": item("s32", profile.get("matchCount", 0)),
                        "bonus_tune_points": item("s32", profile.get("bonusPoints", 0)),
                        "is_bonus_tune_played": item("bool", profile.get("isBonusPlayed", False)),
                    },
                    "last": self._last_profile(profile),
                    "item": self._item_profile(profile),
                    "free_first_play": {
                        "is_available": item(
                            "bool", profile.get("isFirstplay", False)
                        )
                    },
                }
            }
        }

    async def gametop_get_info(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.compress = True
        response.content = {"data": {"info": self._game_info()}}

    async def gametop_get_mdata(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        player = payload.get("player", {})
        jid = content(player.get("jid")) or attr(player, "jid")
        profile = await self._profile_for_jid(jid)
        if profile is None:
            response.status = 109
            return
        scores = await self.data.konami.get_document(profile["refid"], "L44", "score")
        music = []
        grouped = {}
        for score in (scores or {}).get("scores", []):
            key = (score.get("musicId", 0), bool(score.get("isHard", False)))
            grouped.setdefault(key, []).append(score)
        for (music_id, hard), records in grouped.items():
            values = {name: [0, 0, 0] for name in ("score", "clear", "musicRate", "playCount", "clearCount", "fcCount", "exCount")}
            bars = [[0] * 30 for _ in range(3)]
            for record in records:
                seq = min(max(_value(record.get("seq")), 0), 2)
                for name in ("score", "clear", "musicRate", "playCount", "clearCount", "fcCount", "exCount"):
                    values[name][seq] = _value(record.get(name))
                raw_bar = record.get("bar", [])
                if isinstance(raw_bar, list):
                    bars[seq] = raw_bar[:30] + [0] * max(0, 30 - len(raw_bar))
            chart = {
                "score": array("s32", values["score"]),
                "clear": array("s8", values["clear"]),
                "music_rate": array("s32", values["musicRate"]),
                "play_cnt": array("s32", values["playCount"]),
                "clear_cnt": array("s32", values["clearCount"]),
                "fc_cnt": array("s32", values["fcCount"]),
                "ex_cnt": array("s32", values["exCount"]),
                "bar": [array("u8", bar, seq=str(seq)) for seq, bar in enumerate(bars)],
            }
            music.append({"@attr": {"music_id": str(music_id)}, "hard" if hard else "normal": chart})
        response.compress = True
        response.content = {
            "data": {"player": {"jid": item("s32", jid or 0), "mdata_list": {"music": music}}}
        }

    async def gametop_get_meeting(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.compress = True
        response.content = {
            "data": {
                "meeting": {"single": {"@attr": {"count": "0"}}},
                "reward": {"total": item("s32", 0), "point": item("s32", 0)},
            }
        }

    async def gameend_regist(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        player = payload.get("player", {})
        refid = attr(player, "refid") or content(player.get("refid"))
        if not refid:
            response.status = 1
            return
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        for tune in _nodes(payload.get("result", {}).get("tune", [])):
            score = tune.get("player", {}).get("score", {})
            entry = {
                "musicId": _value(tune.get("music")),
                "seq": attr(score, "seq", 0),
                "score": _value(score),
                "clear": attr(score, "clear", 0),
                "musicRate": _value(tune.get("player", {}).get("music_rate")),
                "playCount": _value(tune.get("player", {}).get("play_cnt")),
            }
            document = await self.data.konami.get_document(refid, "L44", "score") or {
                "collection": "score",
                "scores": [],
            }
            existing = next(
                (
                    value
                    for value in document["scores"]
                    if value.get("musicId") == entry["musicId"]
                    and value.get("seq") == entry["seq"]
                ),
                None,
            )
            if existing is None:
                document["scores"].append(entry)
            else:
                existing.update({key: max(existing.get(key, 0), value) for key, value in entry.items() if isinstance(value, int)})
            await self.data.konami.put_document(refid, "L44", "score", document)
        response.compress = True
        response.content = {
            "data": {"player": {"session_id": item("s32", 1)}, "collabo": {"deller": item("s32", 0)}}
        }

    async def shopinfo_regist(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.compress = True
        response.content = {
            "data": {
                "cabid": item("u32", 1),
                "locationid": item("str", "ea"),
                "tax_phase": item("u8", 0),
                "facility": {"exist": item("u32", 0)},
                **self._game_info(),
            }
        }

    async def success(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.status = 0

    async def _profile_for_jid(self, jid):
        if jid is None:
            return None
        for refid, profile in await self.data.konami.documents("L44", "profile"):
            if profile.get("jubeatId") == int(jid):
                profile["refid"] = refid
                return profile
        return None

    @staticmethod
    def _game_info() -> dict:
        return {
            "white_music_list": item("s32", [-1] * 64),
            "white_marker_list": item("s32", [-1] * 16),
            "open_music_list": item("s32", [-1] * 64),
            "expert_option": {"is_available": item("bool", True)},
            "all_music_matching": {"is_available": item("bool", False)},
        }

    @staticmethod
    def _last_profile(profile: dict) -> dict:
        return {
            "music_id": item("s32", profile.get("musicId", 0)),
            "seq_id": item("s8", profile.get("seqId", 0)),
            "sort": item("s8", profile.get("sort", 0)),
            "category": item("s8", profile.get("category", 0)),
            "settings": {
                "marker": item("s8", profile.get("marker", 0)),
                "theme": item("s8", profile.get("theme", 0)),
                "title": item("s16", profile.get("title", 0)),
                "parts": item("s16", profile.get("parts", 0)),
                "rank_sort": item("s8", profile.get("rankSort", 0)),
                "combo_disp": item("s8", profile.get("comboDisp", 0)),
            },
        }

    @staticmethod
    def _item_profile(profile: dict) -> dict:
        return {
            "music_list": array("s32", profile.get("musicList", [-1] * 64)),
            "secret_list": array("s32", profile.get("secretList", [-1] * 64)),
            "theme_list": array("s32", profile.get("themeList", [-1] * 16)),
            "marker_list": array("s32", profile.get("markerList", [-1] * 16)),
            "title_list": array("s32", profile.get("titleList", [-1] * 160)),
            "parts_list": array("s32", profile.get("partsList", [0] * 160)),
        }

    @staticmethod
    def _id(refid: str) -> int:
        return int(hashlib.sha256(f"jubeat:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000


def _nodes(value):
    if isinstance(value, list):
        return value
    return [value] if isinstance(value, dict) else []


def _value(value, default=0):
    if isinstance(value, dict):
        value = value.get("@content", default)
    if isinstance(value, list):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
