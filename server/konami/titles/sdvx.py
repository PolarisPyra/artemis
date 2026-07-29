"""Native baseline handlers for SOUND VOLTEX e-amusement routes."""

from __future__ import annotations

import hashlib
from typing import ClassVar

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn_support.helpers import array, attr, content, item, scalar


class SDVXRoutes:
    """Register the SDVX VI route family used by the current plugin."""

    game_codes: ClassVar[tuple[str, ...]] = ("KFC",)
    _matches: ClassVar[list[dict]] = []

    @classmethod
    def service_modules(cls, game_code: str, model: str = "") -> tuple[str, ...]:
        return ("game", "eventlog", "ins", "package")

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.data = Data(cfg)

    def register(self, router: EamuseRouter) -> None:
        methods = {
            "common": self.game_common,
            "new": self.profile_new,
            "load": self.profile_load,
            "load_m": self.score_load,
            "save": self.profile_save,
            "save_m": self.score_save,
            "save_c": self.course_save,
            "frozen": self.frozen,
            "buy": self.buy,
            "print": self.print_card,
            "hiscore": self.hiscore,
            "load_r": self.rival_load,
            "save_ap": self.mix_save,
            "load_ap": self.mix_load,
            "lounge": self.lounge,
            "shop": self.shop,
            "save_e": self.event_save,
            "save_mega": self.event_save,
            "play_e": self.event_save,
            "play_s": self.event_save,
            "entry_s": self.match_entry,
            "entry_e": self.match_exit,
            "exception": self.event_save,
            "log": self.eventlog_write,
        }
        for code in self.game_codes:
            for method, handler in methods.items():
                router.add(code, "game", f"sv6_{method}", handler)
            router.add(code, "eventlog", "write", self.eventlog_write)
            router.add(code, "package", "list", self.package_list)
            router.add(code, "ins", "netlog", self.success)

    async def game_common(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.compress = True
        response.content = {
            "event": {"info": []},
            "course": {"info": []},
            "extend": {"info": []},
            "valgene": {},
            "music": {"info": []},
        }

    async def profile_new(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = (
            content(payload.get("refid"))
            or content(payload.get("dataid"))
            or attr(payload, "refid", "")
            or attr(payload, "dataid", "")
        )
        if not refid:
            response.status = 1
            return
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            profile = {
                "collection": "profile",
                "sdvxId": self._id(refid),
                "name": "PLAYER",
                "appeal": [],
                "items": [],
                "params": {},
            }
            await self.data.konami.put_profile(refid, profile)
        response.content = {
            "result": item("s32", 0),
            "code": item("s32", profile["sdvxId"]),
            "name": item("str", profile.get("name", "PLAYER")),
        }

    async def profile_load(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = (
            content(payload.get("refid"))
            or content(payload.get("dataid"))
            or attr(payload, "refid", "")
            or attr(payload, "dataid", "")
        )
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        response.content = {
            "result": item("s32", 0),
            "code": item("s32", profile.get("sdvxId", self._id(refid))),
            "name": item("str", profile.get("name", "PLAYER")),
            "profile": {
                "appeal": item("s32", profile.get("appeal", 0)),
                "music_id": item("s32", profile.get("musicID", 0)),
                "music_type": item("s32", profile.get("musicType", 0)),
                "packets": item("s32", profile.get("packets", 0)),
                "blocks": item("s32", profile.get("blocks", 0)),
                "blaster_energy": item("s32", profile.get("blasterEnergy", 0)),
                "blaster_count": item("s32", profile.get("blasterCount", 0)),
            },
        }

    async def score_load(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = (
            content(payload.get("refid"))
            or content(payload.get("dataid"))
            or attr(payload, "refid", "")
            or attr(payload, "dataid", "")
        )
        document = await self.data.konami.get_document(refid, "KFC", "scores") or {}
        music = []
        for score in (document.get("scores", {}) or {}).values():
            music.append({"param": array("u32", self._score_array(score))})
        response.content = {"music": {"info": music}}

    async def profile_save(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = (
            content(payload.get("refid"))
            or content(payload.get("dataid"))
            or attr(payload, "refid", "")
            or attr(payload, "dataid", "")
        )
        if not refid:
            response.status = 1
            return
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        fields = {
            "appeal_id": "appeal", "music_id": "musicID", "music_type": "musicType",
            "sort_type": "sortType", "headphone": "headphone", "blaster_count": "blasterCount",
            "hispeed": "hiSpeed", "lanespeed": "laneSpeed", "gauge_option": "gaugeOption",
            "ars_option": "arsOption", "notes_option": "notesOption",
            "early_late_disp": "earlyLateDisp", "draw_adjust": "drawAdjust",
            "eff_c_left": "effCLeft", "eff_c_right": "effCRight", "narrow_down": "narrowDown",
        }
        for source, target in fields.items():
            if source in payload:
                profile[target] = _value(payload[source])
        await self.data.konami.put_profile(refid, profile)
        response.status = 0

    async def score_save(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = content(payload.get("refid")) or content(payload.get("dataid")) or attr(payload, "refid", "") or attr(payload, "dataid", "")
        if not refid:
            response.status = 1
            return
        document = await self.data.konami.get_document(refid, "KFC", "scores") or {"collection": "scores", "scores": {}}
        scores = document.setdefault("scores", {})
        for track in _nodes(payload.get("track")):
            mid = _value(track.get("music_id"))
            chart = _value(track.get("music_type"))
            if not mid:
                continue
            key = f"{mid}:{chart}"
            old = scores.get(key, {})
            current = {
                "mid": mid, "type": chart,
                "score": max(_value(old.get("score")), _value(track.get("score"))),
                "exscore": max(_value(old.get("exscore")), _value(track.get("exscore"))),
                "clear": max(_value(old.get("clear")), _value(track.get("clear_type"))),
                "grade": max(_value(old.get("grade")), _value(track.get("score_grade"))),
                "buttonRate": max(_value(old.get("buttonRate")), _value(track.get("btn_rate"))),
                "longRate": max(_value(old.get("longRate")), _value(track.get("long_rate"))),
                "volRate": max(_value(old.get("volRate")), _value(track.get("vol_rate"))),
                "volforce": max(_value(old.get("volforce")), _value(track.get("volforce"))),
            }
            scores[key] = current
        await self.data.konami.put_document(refid, "KFC", "scores", document)
        response.status = 0

    async def course_save(self, info, data, response):
        payload = data.get("data", data)
        refid = self._refid(payload)
        if not refid:
            response.status = 1
            return
        document = await self.data.konami.get_document(refid, "KFC", "courses") or {
            "collection": "courses", "courses": {}
        }
        records = document.setdefault("courses", {})
        for course in _nodes(payload.get("course") or payload.get("record")):
            course_id = _value(course.get("course_id") or course.get("crsid"))
            if course_id:
                records[str(course_id)] = {
                    key: _value(course.get(key))
                    for key in ("course_id", "crsid", "score", "clear_type", "grade", "count")
                    if key in course
                }
        await self.data.konami.put_document(refid, "KFC", "courses", document)
        response.status = 0

    async def hiscore(self, info, data, response):
        payload = data.get("data", data)
        limit = _value(payload.get("limit"), 100000)
        offset = _value(payload.get("offset"))
        rows = []
        for refid, document in await self.data.konami.documents("KFC", "scores"):
            profile = await self.data.konami.get_profile(refid) or {}
            for score in (document.get("scores", {}) or {}).values():
                mid = _value(score.get("mid"))
                if offset < mid <= offset + limit:
                    code = str(profile.get("sdvxId", self._id(refid)))
                    name = str(profile.get("name", "PLAYER"))
                    rows.append({
                        "id": item("u32", mid), "ty": item("u32", _value(score.get("type"))),
                        "a_sq": item("str", code), "a_nm": item("str", name),
                        "a_sc": item("u32", _value(score.get("score"))),
                        "l_sq": item("str", code), "l_nm": item("str", name),
                        "l_sc": item("u32", _value(score.get("score"))),
                        "ax_sq": item("str", code), "ax_nm": item("str", name),
                        "ax_sc": item("u32", _value(score.get("exscore"))),
                        "lx_sq": item("str", code), "lx_nm": item("str", name),
                        "lx_sc": item("u32", _value(score.get("exscore"))),
                        "avg_sc": item("u32", _value(score.get("score"))),
                        "avg_ex": item("u32", _value(score.get("exscore"))),
                        "cr": item("s32", 8763),
                        "avg_sc_lv": array("u32", [_value(score.get("score"))] * 13),
                        "avg_ex_lv": array("u32", [_value(score.get("exscore"))] * 13),
                    })
        response.content = {"sc": {"d": rows}}

    async def rival_load(self, info, data, response):
        payload = data.get("data", data)
        refid = self._refid(payload)
        rivals = []
        for index, (other, profile) in enumerate(await self.data.konami.documents("KFC", "profile")):
            if other == refid:
                continue
            scores = await self.data.konami.get_document(other, "KFC", "scores") or {}
            rivals.append({
                "no": item("s16", index), "seq": item("str", str(profile.get("sdvxId", self._id(other)))),
                "name": item("str", str(profile.get("name", "PLAYER"))),
                "music": {"param": [
                    array("u32", self._score_array(score))
                    for score in (scores.get("scores", {}) or {}).values()
                ]},
            })
        response.content = {"rival": rivals}

    async def mix_save(self, info, data, response):
        payload = data.get("data", data)
        refid = self._refid(payload)
        if not refid:
            response.status = 1
            return
        mix = payload.get("automation", payload)
        document = await self.data.konami.get_document(refid, "KFC", "mix") or {"mixes": {}}
        code = str(content(mix.get("mix_code")) or _value(mix.get("mix_id")) or self._id(refid))
        record = {key: _value(mix.get(key)) if key.endswith("_id") or key == "tag_bit" else content(mix.get(key), "")
                  for key in ("mix_id", "mix_name", "generate_param", "jacket_id", "tag_bit") if key in mix}
        record["mix_code"] = code
        document.setdefault("mixes", {})[code] = record
        await self.data.konami.put_document(refid, "KFC", "mix", document)
        response.content = {"automation": self._mix_response(record, code, refid)}

    async def mix_load(self, info, data, response):
        payload = data.get("data", data)
        refid = self._refid(payload)
        mix = payload.get("automation", payload)
        code = str(content(mix.get("mix_code")) or "")
        document = await self.data.konami.get_document(refid, "KFC", "mix") or {}
        record = (document.get("mixes", {}) or {}).get(code)
        response.content = {"result": item("s32", 1)} if record is None else {"automation": self._mix_response(record, code, refid)}

    async def frozen(self, info, data, response):
        response.content = {"result": item("s32", 0)}

    async def buy(self, info, data, response):
        response.content = {"result": item("s32", 0)}

    async def print_card(self, info, data, response):
        response.content = {"result": item("s32", 0), "print_state": item("s32", 0)}

    async def event_save(self, info, data, response):
        payload = data.get("data", data)
        refid = self._refid(payload)
        if refid:
            document = await self.data.konami.get_document(refid, "KFC", "events") or {
                "collection": "events", "events": []
            }
            event = {key: _value(value) if key.endswith(("id", "no", "type", "score")) else content(value, "")
                     for key, value in payload.items() if not key.startswith("@")}
            document.setdefault("events", []).append(event)
            document["events"] = document["events"][-100:]
            await self.data.konami.put_document(refid, "KFC", "events", document)
        response.status = 0

    async def match_entry(self, info, data, response):
        payload = data.get("data", data)
        now = __import__("time").time()
        SDVXRoutes._matches = [m for m in SDVXRoutes._matches if now - m["time"] < 90]
        game_id = _value(payload.get("mid")); filter_id = _value(payload.get("filter"))
        gip = _bytes(payload.get("gip")); lip = _bytes(payload.get("lip"))
        current = {"mid": game_id, "filter": filter_id, "gip": gip, "lip": lip, "port": _value(payload.get("port")), "time": now}
        if not any(m["mid"] == game_id and m["filter"] == filter_id and m["gip"] == gip for m in SDVXRoutes._matches):
            SDVXRoutes._matches.append(current)
        response.content = {"entry_id": item("u32", 0), "entry": [
            {"gip": item("4u8", m["gip"]), "lip": item("4u8", m["lip"]), "port": item("u16", m["port"])}
            for m in SDVXRoutes._matches if m["mid"] == game_id and m["filter"] == filter_id and m is not current
        ]}

    async def match_exit(self, info, data, response):
        response.status = 0

    async def lounge(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"interval": item("u32", 30)}

    async def shop(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"nxt_time": item("u32", 1500)}

    async def eventlog_write(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "gamesession": item("s64", 1),
            "logsendflg": item("s32", 0),
            "logerrlevel": item("s32", 0),
            "evtidnosendflg": item("s32", 0),
        }

    async def package_list(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"package": {"@attr": {"expire": "1200", "status": "1"}}}

    async def success(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.status = 0

    @staticmethod
    def _id(refid: str) -> int:
        return int(hashlib.sha256(f"sdvx:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000

    @staticmethod
    def _refid(payload: dict) -> str:
        return (
            content(payload.get("refid")) or content(payload.get("ref_id"))
            or content(payload.get("dataid")) or attr(payload, "refid", "")
            or attr(payload, "ref_id", "") or attr(payload, "dataid", "")
        )

    @staticmethod
    def _mix_response(record: dict, code: str, refid: str) -> dict:
        return {
            "mix_id": item("s32", _value(record.get("mix_id"), SDVXRoutes._id(code))),
            "mix_code": item("str", code), "seq": item("str", code),
            "mix_name": item("str", str(record.get("mix_name", ""))),
            "player_name": item("str", str(record.get("player_name", "PLAYER"))),
            "generate_param": item("str", str(record.get("generate_param", ""))),
            "distribution_date": item("u32", 19990101),
            "jacket_id": item("s32", _value(record.get("jacket_id"))),
            "tag_bit": item("s32", _value(record.get("tag_bit"))),
            "like_flg": item("bool", 0),
        }

    @staticmethod
    def _score_array(score: dict) -> list[int]:
        return [
            _value(score.get("mid")), _value(score.get("type")), _value(score.get("score")),
            _value(score.get("exscore")), _value(score.get("clear")), _value(score.get("grade")),
            0, 0, _value(score.get("buttonRate")), _value(score.get("longRate")),
            _value(score.get("volRate")), _value(score.get("volforce")), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ]


def _nodes(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _value(value, default=0):
    if isinstance(value, dict):
        value = content(value, attr(value, "value", default))
    return scalar(value, default)


def _bytes(value) -> list[int]:
    value = content(value, value)
    if isinstance(value, (bytes, bytearray)):
        return list(value[:4]) + [0] * max(0, 4 - len(value))
    if isinstance(value, list):
        return [scalar(v) & 0xFF for v in value[:4]] + [0] * max(0, 4 - len(value))
    if isinstance(value, str):
        parts = value.replace(".", ",").split(",")
        return [scalar(v) & 0xFF for v in parts[:4]] + [0] * max(0, 4 - len(parts))
    return [0, 0, 0, 0]
