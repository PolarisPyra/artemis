"""Native baseline handlers for the IIDX e-amusement route family.

The IIDX hook supports many revisions, but the wire contract is shared by the
GLD through LDJ model families.  Keep the route registration in one place so
additional version payloads can be added without changing service discovery.
"""

from __future__ import annotations

import hashlib
from typing import ClassVar

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn import array, attr, content, item, scalar


class IIDXRoutes:
    """Register the common IIDX PC/shop/music route surface."""

    game_codes: ClassVar[tuple[str, ...]] = ("JDJ", "JDZ", "KDZ", "LDJ")

    _version_by_code: ClassVar[dict[str, int]] = {
        "JDJ": 17,
        "JDZ": 18,
        "KDZ": 19,
        "LDJ": 20,
    }

    @classmethod
    def service_modules(cls, game_code: str, model: str = "") -> tuple[str, ...]:
        return (
            "pc",
            "shop",
            "music",
            "grade",
            "ranking",
            "gameSystem",
        )

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.data = Data(cfg)

    def register(self, router: EamuseRouter) -> None:
        multi_routes = {
            "pc": (
                "common",
                "reg",
                "get",
                "getname",
                "oldget",
                "takeover",
                "visit",
                "save",
                "shopregister",
                "getLaneGachaTicket",
                "drawLaneGacha",
                "consumeLaneGachaTicket",
            ),
            "shop": ("getname", "savename", "getconvention", "setconvention"),
            "music": (
                "crate",
                "getrank",
                "getralive",
                "appoint",
                "reg",
                "breg",
                "arenaCPU",
            ),
            "grade": ("raised",),
            "ranking": ("entry", "oentry", "getranker"),
            "gameSystem": ("systemInfo",),
        }
        handlers = {
            ("pc", "common"): self.pc_common,
            ("pc", "reg"): self.pc_reg,
            ("pc", "get"): self.pc_get,
            ("pc", "getname"): self.pc_getname,
            ("pc", "visit"): self.pc_visit,
            ("pc", "save"): self.pc_save,
            ("music", "reg"): self.music_reg,
            ("music", "breg"): self.music_reg,
            ("music", "getrank"): self.music_getrank,
            ("music", "getralive"): self.music_getralive,
            ("music", "crate"): self.music_crate,
            ("music", "appoint"): self.music_appoint,
            ("grade", "raised"): self.grade_raised,
            ("pc", "oldget"): self.pc_get,
            ("pc", "takeover"): self.pc_get,
            ("pc", "shopregister"): self.pc_shopregister,
            ("pc", "getLaneGachaTicket"): self.lane_gacha,
            ("pc", "drawLaneGacha"): self.lane_gacha,
            ("pc", "consumeLaneGachaTicket"): self.lane_gacha,
            ("shop", "getname"): self.shop_info,
            ("shop", "savename"): self.shop_info,
            ("shop", "getconvention"): self.shop_info,
            ("shop", "setconvention"): self.shop_info,
            ("music", "arenaCPU"): self.arena_cpu,
            ("ranking", "entry"): self.ranking_entry,
            ("ranking", "oentry"): self.ranking_entry,
            ("ranking", "getranker"): self.ranking_getranker,
            ("gameSystem", "systemInfo"): self.system_info,
        }
        for code in self.game_codes:
            for module, methods in multi_routes.items():
                for method in methods:
                    router.add(
                        code,
                        module,
                        method,
                        handlers.get((module, method), self.success),
                    )
            if code == "LDJ":
                # Later IIDX revisions prefix the same module with IIDX21
                # through IIDX32.  Asphyxia registers both forms.
                for version in range(21, 33):
                    for module, methods in multi_routes.items():
                        for method in methods:
                            router.add(
                                code,
                                f"IIDX{version}{module}",
                                method,
                                handlers.get((module, method), self.success),
                            )

    async def pc_common(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        """Return the common phase/options object expected during IIDX boot."""
        version = self._version(info)
        content = {
            "@attr": {"expire": "300"},
            "ir": {"@attr": {"beat": "3"}},
            "expert": {"@attr": {"phase": "2"}},
            "expert_random_secret": {"@attr": {"phase": "2"}},
            "expert_secret_full_open": {},
        }
        command = {
            "gmbl": "1",
            "gmbla": "1",
            "regl": "1",
            "rndp": "1",
            "hrnd": "1",
            "alls": "1",
        }
        if version == 14:
            content["gshop"] = {"@attr": {"vipg": "0"}}
        elif version in (16, 17, 18):
            content["cmd"] = {"@attr": command}
            if version >= 17:
                content["lg"] = {"@attr": {"lea": "0"}}
            if version == 18:
                content.update(
                    {
                        "lf": {"@attr": {"life": "0"}},
                        "ev": {"@attr": {"pha": "3"}},
                        "lincle": {"@attr": {"phase": "1"}},
                    }
                )
        elif version == 19:
            content.update(
                {
                    "lincle": {"@attr": {"phase": "2"}},
                    "boss": {"@attr": {"phase": "2"}},
                    "mr_secret": {"@attr": {"flg": "-1"}},
                    "travel": {"@attr": {"flg": "-1"}},
                }
            )
        elif version >= 20:
            content.update(
                {
                    "limit": {"@attr": {"phase": "24"}},
                    "boss": {"@attr": {"phase": "3"}},
                    "deller_bonus": {"@attr": {"open": "1"}},
                    "newsong_another": {"@attr": {"open": "1"}},
                    "vip_pass_black": {},
                }
            )
            if version >= 22:
                content["license"] = {"string": item("bin", b"\x00")}
            if version >= 27:
                content.update(
                    {
                        "movie_agreement": {"@attr": {"version": "1"}},
                        "premium_area_news": {"@attr": {"open": "1"}},
                        "premium_area_qpro": {"@attr": {"open": "1"}},
                        "play_video": {},
                    }
                )
            if version == 20:
                content.update(
                    {
                        "red": {"@attr": {"phase": "1"}},
                        "yellow": {"@attr": {"phase": "1"}},
                        "medal": {"@attr": {"phase": "1"}},
                        "cafe": {"@attr": {"open": "1"}},
                        "tricolettepark": {"@attr": {"open": "1"}},
                    }
                )
            elif version == 21:
                content.update(
                    {
                        "boss1": {"@attr": {"phase": "1"}},
                        "medal": {"@attr": {"phase": "1"}},
                        "cafe": {"@attr": {"open": "1"}},
                        "tricolettepark": {"@attr": {"open": "1"}},
                        "tricolettepark_skip": {"@attr": {"phase": "1"}},
                        "gumi_event": {},
                        "superstar": {"@attr": {"phase": "1"}},
                    }
                )
            elif version == 22:
                content.update(
                    {
                        "pre_play": {"@attr": {"phase": "1"}},
                        "toho_remix": {"@attr": {"phase": "1"}},
                        "chrono_diver": {"@attr": {"phase": "1"}},
                        "qpronicle_chord": {"@attr": {"phase": "1"}},
                        "cc_collabo_event": {"@attr": {"phase": "1"}},
                        "cc_collabo_license": {},
                        "common_timeshift_phase": {"@attr": {"phase": "1"}},
                        "eappli_expert": {},
                        "eaorder": {},
                    }
                )
            elif version == 23:
                content.update(
                    {
                        "event1_phase": {"@attr": {"phase": "1"}},
                        "event2_phase": {"@attr": {"phase": "1"}},
                        "extra_boss_event": {"@attr": {"phase": "1"}},
                        "event1_ranbow_ticket": {},
                        "remocon_collabo": {},
                        "ravemania_collabo": {},
                        "djlevel_result": {},
                        "virtual_coin": {"@attr": {"phase": "1"}},
                        "reflec_volzza_collabo": {},
                        "bemani_summer2016": {"@attr": {"phase": "1"}},
                    }
                )
            elif version in (24, 25, 26):
                content.update(
                    {
                        "extra_boss_event": {"@attr": {"phase": "1"}},
                        "event1_phase": {"@attr": {"phase": "1"}},
                        "event2_phase": {"@attr": {"phase": "1"}},
                        "eaorder_phase": {"@attr": {"phase": "2"}},
                        "common_evnet": {"@attr": {"flg": "-1"}},
                    }
                )
            if version >= 28:
                content.update(
                    {
                        "movie_upload": {"@attr": {"url": ""}},
                        "eisei": {"@attr": {"open": "1"}},
                        "eaorder_phase": {"@attr": {"phase": "2"}},
                        "common_evnet": {"@attr": {"flg": "-1"}},
                        "world_tourism": {"@attr": {"open_list": "-1"}},
                        "bpl_battle": {"@attr": {"phase": "1"}},
                        "display_asio_logo": {},
                    }
                )
            if version >= 29:
                content["lane_gacha"] = {}
            if version >= 30:
                content["music_retry"] = {}
            if version >= 31:
                content["tourism_booster"] = {}
        response.content = content

    async def pc_reg(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "")
        if not refid:
            response.status = 1
            return
        version = self._version(info)
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            numeric_id = self._id(refid)
            profile = {
                "collection": "profile",
                "name": "PLAYER",
                "id": numeric_id,
                "idstr": f"{numeric_id:08d}"[:4] + "-" + f"{numeric_id:08d}"[4:],
                "pid": 0,
                "language": -1,
                "total_pc": 0,
                "total_kbd": 0,
                "total_scr": 0,
            }
            await self.data.konami.put_profile(refid, profile)
        pcdata = await self.data.konami.get_document(refid, info.game_code, "pcdata", str(version))
        if pcdata is None:
            await self.data.konami.put_document(
                refid,
                info.game_code,
                "pcdata",
                {"collection": "pcdata", "version": version, "spnum": 0, "dpnum": 0},
                str(version),
            )
        response.content = {
            "@attr": {
                "id": str(profile["id"]),
                "id_str": profile["idstr"],
            }
        }

    async def pc_get(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        response.content = {
            "@attr": {"id": str(profile.get("id", self._id(refid)))},
            "name": item("str", profile.get("name", "PLAYER")),
            "idstr": item("str", profile.get("idstr", "0000-0000")),
            "pid": item("s32", profile.get("pid", 0)),
        }

    async def pc_getname(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        response.content = {
            "@attr": {
                "name": profile.get("name", "PLAYER"),
                "idstr": profile.get("idstr", "0000-0000"),
                "pid": str(profile.get("pid", 0)),
            }
        }

    async def pc_visit(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "@attr": {
                "anum": "10",
                "snum": "10",
                "pnum": "10",
                "aflg": "0",
                "sflg": "0",
                "pflg": "0",
            }
        }

    async def pc_save(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "") or content(data.get("rid"))
        if not refid:
            response.status = 1
            return
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        # pc.save carries the mutable profile fields as typed leaf nodes. Keep
        # unknown fields intact so newer revisions can round-trip settings we
        # do not interpret yet.
        for name in (
            "name", "pid", "spnum", "dpnum", "deller", "qprodata", "skin", "config",
            "play_style", "sgrade", "dgrade", "sgrade_c", "dgrade_c",
        ):
            if name in data:
                value = content(data[name], data[name])
                profile[name] = value[0] if isinstance(value, list) and len(value) == 1 else value
        await self.data.konami.put_profile(refid, profile)
        pcdata = await self.data.konami.get_document(
            refid, info.game_code, "pcdata", str(self._version(info))
        ) or {"collection": "pcdata", "version": self._version(info)}
        for name in ("spnum", "dpnum", "deller", "qprodata", "skin", "config"):
            if name in data:
                pcdata[name] = content(data[name], data[name])
        await self.data.konami.put_document(
            refid, info.game_code, "pcdata", pcdata, str(self._version(info))
        )
        response.status = 0

    async def music_reg(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "") or content(data.get("rid"))
        if not refid:
            response.status = 1
            return
        document = await self.data.konami.get_document(refid, info.game_code, "score") or {
            "collection": "score", "scores": {}
        }
        for node in _nodes(data.get("m", data.get("music", []))):
            song_id = scalar(attr(node, "mid", attr(node, "music_id", 0)))
            if not song_id:
                song_id = scalar(content(node), 0)
            if not song_id:
                continue
            entry = {
                "score": scalar(content(node.get("score")), scalar(content(node), 0)),
                "clear_type": scalar(
                    content(node.get("clear", node.get("clear_type"))), 0
                ),
                "cnt": scalar(content(node.get("cnt")), 0),
            }
            current = document["scores"].get(str(song_id), {})
            document["scores"][str(song_id)] = {
                **current,
                "score": max(scalar(current.get("score"), 0), entry["score"]),
                "clear_type": max(scalar(current.get("clear_type"), 0), entry["clear_type"]),
                "cnt": max(scalar(current.get("cnt"), 0), entry["cnt"]),
            }
        await self.data.konami.put_document(refid, info.game_code, "score", document)
        response.status = 0

    async def music_getrank(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "") or content(data.get("rid"))
        document = await self.data.konami.get_document(refid, info.game_code, "score") or {}
        rows = []
        beginner = []
        for song_id, score in (document.get("scores", {}) or {}).items():
            mid = scalar(song_id)
            rows.append(array("s16", [-1, mid, scalar(score.get("score")), scalar(score.get("score")), scalar(score.get("clear_type"))]))
            if scalar(score.get("clear_type")):
                beginner.append(array("u16", [mid, scalar(score.get("clear_type"))]))
        response.content = {"style": {"@attr": {"type": str(scalar(attr(data, "cltype"), 0))}}, "m": rows, "b": beginner, "top": []}

    async def music_getralive(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = attr(data, "rid", "") or content(data.get("rid"))
        document = await self.data.konami.get_document(refid, info.game_code, "score") or {}
        response.content = {
            "d": [array("s16", [scalar(song_id), scalar(score.get("score")), scalar(score.get("clear_type"))])
                  for song_id, score in (document.get("scores", {}) or {}).items()]
        }

    async def music_crate(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        """Return per-chart clear/full-combo rates from all stored scores."""
        version = self._version(info)
        totals: dict[int, list[int]] = {}
        clears: dict[int, list[int]] = {}
        fulls: dict[int, list[int]] = {}
        for _, document in await self.data.konami.documents(info.game_code, "score"):
            for song_id, score in (document.get("scores", {}) or {}).items():
                mid = scalar(song_id)
                if mid // 1000 > version:
                    continue
                chart = scalar(score.get("chart"), 0)
                totals.setdefault(mid, [0] * 10)[chart] += 1
                clear = scalar(score.get("clear_type"))
                clears.setdefault(mid, [0] * 10)[chart] += int(clear != 1)
                fulls.setdefault(mid, [0] * 10)[chart] += int(clear >= 7)
        rows = []
        for mid in sorted(totals):
            total = totals[mid]; clear = clears[mid]; full = fulls[mid]
            rates = []
            for values in (clear, full):
                rates.extend([round(values[index] * 1000 / total[index]) if total[index] else 0 for index in range(10)])
            rows.append(array("s32", rates, mid=str(mid)))
        response.content = {"c": rows}

    async def music_appoint(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = attr(payload, "rid", "") or attr(payload, "refid", "") or content(payload.get("rid"))
        mid = scalar(attr(payload, "mid", 0))
        document = await self.data.konami.get_document(refid, info.game_code, "score") or {}
        score = (document.get("scores", {}) or {}).get(str(mid))
        if score is None:
            response.status = 0
            return
        response.content = {
            "mydata": item("bin", bytes(_pack_score(score)), score=str(scalar(score.get("score"))))
        }

    async def grade_raised(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = attr(payload, "rid", "") or attr(payload, "refid", "") or content(payload.get("rid"))
        if not refid:
            response.status = 1
            return
        version = str(self._version(info)); gid = scalar(attr(payload, "gid", 0)); gtype = scalar(attr(payload, "gtype", 0))
        document = await self.data.konami.get_document(refid, info.game_code, "grade", version) or {"grades": {}}
        key = f"{gtype}:{gid}"; old = (document.setdefault("grades", {})).get(key, {})
        current = {"maxStage": max(scalar(old.get("maxStage")), scalar(attr(payload, "cflg", 0))),
                   "archive": max(scalar(old.get("archive")), scalar(attr(payload, "achi", 0)))}
        document["grades"][key] = current
        await self.data.konami.put_document(refid, info.game_code, "grade", document, version)
        response.content = {"@attr": {"pnum": "1"}}

    async def pc_shopregister(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"@attr": {"pnum": "1"}}

    async def lane_gacha(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "ticket": item("s32", 0),
            "ticket_num": item("s32", 0),
            "result": item("s32", 0),
        }

    async def shop_info(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "shop": {
                "name": item("str", "ARTEMIS"),
                "pref": item("s32", 0),
                "pid": item("s32", 0),
            }
        }

    async def arena_cpu(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"cpu": []}

    async def ranking_entry(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"@attr": {"anum": "0", "jun": "0"}}

    async def ranking_getranker(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {"ranker": []}

    async def system_info(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "@attr": {"expire": "600"},
            "ir": {"@attr": {"phase": "0"}},
        }

    async def success(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.status = 0

    def _version(self, info: EamuseInfo) -> int:
        base = self._version_by_code.get(info.game_code, 20)
        if info.game_code == "LDJ" and info.module.startswith("IIDX"):
            try:
                version = int(info.module[4:6])
            except ValueError:
                return base
            if 20 <= version <= 32:
                return version
        return base

    @staticmethod
    def _id(refid: str) -> int:
        return int(hashlib.sha256(f"iidx:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000


def _nodes(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _pack_score(score: dict) -> list[int]:
    """Provide a stable minimal ghost blob for music.appoint consumers."""
    value = scalar(score.get("score"))
    clear = scalar(score.get("clear_type"))
    return [value & 0xFF, (value >> 8) & 0xFF, clear & 0xFF, 0]
