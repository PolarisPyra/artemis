"""Pop'n Music e-amusement implementation and versioned protocol handlers."""

from __future__ import annotations

import hashlib
import random
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data


def attr(node: Any, name: str, default: Any = None) -> Any:
    if not isinstance(node, dict):
        return default
    return node.get("@attr", {}).get(name, default)


def content(node: Any, default: Any = None) -> Any:
    if not isinstance(node, dict) or "@content" not in node:
        return default
    value = node["@content"]
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def child(node: Any, name: str, default: Any = None) -> Any:
    if not isinstance(node, dict):
        return default
    return node.get(name, default)


def item(type_name: str, value: Any, **extra: Any) -> dict:
    return {
        "@attr": {"__type": type_name, **extra},
        "@content": value if isinstance(value, (list, bytes, bytearray)) else [value],
    }


def array(type_name: str, value: list[Any], **extra: Any) -> dict:
    return {
        "@attr": {"__type": type_name, "__count": len(value), **extra},
        "@content": value,
    }


def scalar(value: Any, default: Any = 0) -> Any:
    try:
        if value is None:
            return default
        if isinstance(value, list):
            value = value[0] if value else default
        return int(value)
    except (TypeError, ValueError):
        return default


def walk_get(node: Any, path: str, default: Any = None) -> Any:
    current = node
    for part in path.split(".") if path else ():
        if isinstance(current, list):
            current = current[0] if current else None
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return default if current is None else current


def walk_set(node: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    current = node
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


DEFAULT_FIELDS = {
    "v24": [
        ("play_id", "s32", "account", 0, False),
        ("start_type", "s8", "account", 0, False),
        ("tutorial", "s16", "account", -1, False),
        ("area_id", "s16", "account", 51, False),
        ("read_news", "s16", "account", 0, False),
        (
            "nice",
            "s16",
            "account",
            [
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
            ],
            True,
        ),
        (
            "favorite_chara",
            "s16",
            "account",
            [
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
                -1,
            ],
            True,
        ),
        ("special_area", "s16", "account", [-1, -1, -1, -1, -1, -1, -1, -1], True),
        ("chocolate_charalist", "s16", "account", [-1, -1, -1, -1, -1], True),
        ("chocolate_sp_chara", "s32", "account", 0, False),
        ("chocolate_pass_cnt", "s32", "account", 0, False),
        ("chocolate_hon_cnt", "s32", "account", 0, False),
        ("chocolate_giri_cnt", "s32", "account", 0, False),
        ("chocolate_kokyu_cnt", "s32", "account", 0, False),
        (
            "teacher_setting",
            "s16",
            "account",
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            True,
        ),
        ("welcom_pack", "bool", "account", 0, False),
        ("use_navi", "s16", "account", 0, False),
        ("ranking_node", "s32", "account", 0, False),
        ("chara_ranking_kind_id", "s32", "account", 0, False),
        ("navi_evolution_flg", "s8", "account", 0, False),
        ("ranking_news_last_no", "s32", "account", 0, False),
        ("power_point", "s32", "account", 0, False),
        ("player_point", "s32", "account", 300, False),
        ("power_point_list", "s32", "account", [0], True),
        ("mode", "u8", "config", 0, False),
        ("chara", "s16", "config", 0, False),
        ("music", "s16", "config", 0, False),
        ("sheet", "u8", "config", 0, False),
        ("category", "s8", "config", 0, False),
        ("sub_category", "s8", "config", 0, False),
        ("chara_category", "s8", "config", 0, False),
        ("disp_setting", "s8", "config", 0, False),
        ("ms_banner_disp", "s8", "config", 0, False),
        ("ms_down_info", "s8", "config", 0, False),
        ("ms_side_info", "s8", "config", 0, False),
        ("ms_raise_type", "s8", "config", 0, False),
        ("ms_rnd_type", "s8", "config", 0, False),
        ("banner_sort", "s8", "config", 0, False),
        ("course_id", "s16", "config", 0, False),
        ("course_folder", "s8", "config", 0, False),
        ("hispeed", "s16", "option", 10, False),
        ("popkun", "u8", "option", 0, False),
        ("hidden", "bool", "option", 0, False),
        ("hidden_rate", "s16", "option", -1, False),
        ("sudden", "bool", "option", 0, False),
        ("sudden_rate", "s16", "option", -1, False),
        ("randmir", "s8", "option", 0, False),
        ("gauge_type", "s8", "option", 0, False),
        ("judge_ad", "s8", "option", 0, False),
        ("ojama_0", "u8", "option", 0, False),
        ("ojama_1", "u8", "option", 0, False),
        ("forever_0", "bool", "option", 0, False),
        ("forever_1", "bool", "option", 0, False),
        ("full_setting", "bool", "option", 0, False),
        ("guide_se", "s8", "option", 0, False),
        ("judge", "u8", "option", 0, False),
        ("ep", "u16", "info", 0, False),
        ("effect_left", "u16", "customize", 0, False),
        ("effect_center", "u16", "customize", 0, False),
        ("effect_right", "u16", "customize", 0, False),
        ("hukidashi", "u16", "customize", 0, False),
        ("comment_1", "u16", "customize", 0, False),
        ("comment_2", "u16", "customize", 0, False),
        ("card_again_count", "s16", "account", 0, False),
        ("sp_riddles_id", "s16", "account", -1, False),
        ("point", "u32", "event2021", 0, False),
        ("step", "u8", "event2021", 0, False),
        ("quest_point", "u32", "event2021", [0, 0, 0, 0, 0, 0, 0, 0], True),
        ("step_nos", "u8", "event2021", 0, False),
        (
            "quest_point_nos",
            "u32",
            "event2021",
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            True,
        ),
        ("lift", "bool", "option", 0, False),
        ("lift_rate", "s16", "option", 0, False),
        ("team_id", "s16", "event_p27", 0, False),
        ("select_battery_id", "s16", "event_p27", 1, False),
        ("today_first_play", "bool", "event_p27", 1, False),
    ],
}


class PopnRepository:
    def __init__(self, data: Data, game_code: str) -> None:
        self.data = data
        # M39 is the shared modern Pop'n profile namespace. The requested
        # game code is retained for legacy document compatibility.
        self.game_code = game_code
        self.profile_code = "M39"

    async def profile(self, refid: str) -> dict:
        profile = await self.data.konami.get_profile(refid)
        should_save = False
        if profile is None:
            profile = await self.data.konami.get_document(refid, self.game_code, "profile")
            should_save = profile is not None
        if profile is None and self.game_code != self.profile_code:
            profile = await self.data.konami.get_document(
                refid, self.profile_code, "profile"
            )
            should_save = profile is not None
        if profile is None:
            return {
                "collection": "profile",
                "name": "ゲスト",
                "friendId": self._friend_id(refid),
                "dataVersion": 2,
            }
        if not profile.get("friendId"):
            profile["friendId"] = self._friend_id(refid)
            should_save = True
        if should_save:
            await self.data.konami.put_profile(refid, profile)
        return profile

    @staticmethod
    def _friend_id(refid: str) -> str:
        value = int(hashlib.sha256(f"friend:{refid}".encode()).hexdigest()[:12], 16)
        return f"{value % 1_000_000_000_000:012d}"

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
        sharing_enabled = self.data.config.konami.enable_score_sharing
        versions = (
            [version]
            if force_version or not sharing_enabled
            else [f"v{i}" for i in range(19, 28)]
        )
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
        rival_profile = await self.data.konami.get_profile(rivalid)
        if rival_profile is None:
            rival_profile = await self.data.konami.get_document(
                rivalid, self.game_code, "profile"
            )
        if rival_profile is None and self.game_code != self.profile_code:
            rival_profile = await self.data.konami.get_document(
                rivalid, self.profile_code, "profile"
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


CLEAR_TO_MEDAL = {
    100: 1,
    200: 2,
    300: 3,
    400: 4,
    500: 5,
    600: 6,
    700: 7,
    800: 8,
    900: 9,
    1000: 10,
    1100: 11,
}
MEDAL_TO_CLEAR = {value: key for key, value in CLEAR_TO_MEDAL.items()}
N_DATA_CLEAR = {
    1: 100,
    2: 200,
    3: 300,
    5: 500,
    6: 600,
    7: 700,
    9: 800,
    10: 900,
    11: 1000,
    15: 1100,
}


def field(data: dict, name: str, default: Any = None) -> Any:
    value = attr(data, name, None)
    if value is None:
        value = content(child(data, name), None)
    return default if value is None else value


def elements(data: dict, name: str) -> list[dict]:
    value = child(data, name, [])
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


@dataclass(frozen=True)
class VersionSpec:
    version: str
    max_music: int


SPECS = {
    "v27": VersionSpec("v27", 2188),
}

PHASES = {
    "v27": [
        (0, 6),
        (1, 6),
        (2, 4),
        (3, 0),
        (4, 7),
        (5, 48),
        (6, 2),
        (7, 6),
        (8, 2),
        (9, 44),
        (10, 1),
        (11, 2),
        (12, 2),
        (13, 2),
    ],
}


class PopnVersionHandler:
    def __init__(
        self, repository: PopnRepository, spec: VersionSpec, force_unlock: bool = True
    ) -> None:
        self.repo = repository
        self.spec = spec
        self.force_unlock = force_unlock

    async def info(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        if self.spec.version == "v19":
            response.content = {
                "@attr": {
                    "game_phase": "2",
                    "ir_phase": "14",
                    "event_phase": "15",
                    "netvs_phase": "18",
                    "card_phase": "3",
                    "gfdm_phase": "2",
                    "jubeat_phase": "2",
                    "local_matching_enable": "0",
                    "matching_sec": "120",
                    "boss_diff": ",".join(["100"] * 10),
                    "boss_battle_point": "1",
                }
            }
        elif self.spec.version == "v20":
            response.content = self._items(
                {
                    "game_phase": ("s32", 2),
                    "ir_phase": ("s32", 0),
                    "event_phase": ("s32", 5),
                    "netvs_phase": ("s32", 0),
                    "card_phase": ("s32", 6),
                    "illust_phase": ("s32", 2),
                    "psp_phase": ("s32", 5),
                    "other_phase": ("s32", 1),
                    "jubeat_phase": ("s32", 1),
                    "public_phase": ("s32", 3),
                    "kac_phase": ("s32", 2),
                    "local_matching": ("s32", 0),
                    "n_matching_sec": ("s32", 60),
                    "l_matching_sec": ("s32", 60),
                    "is_check_cpu": ("s32", 0),
                    "week_no": ("s32", 0),
                }
            )
            response.content.update(
                {
                    "ng_illust": array("s32", [0] * 10),
                    "sel_ranking": array("s16", [-1] * 10),
                    "up_ranking": array("s16", [-1] * 10),
                }
            )
        elif self.spec.version == "v21":
            response.content = self._items(
                {
                    "ir_phase": ("s32", 0),
                    "music_open_phase": ("s32", 8),
                    "collabo_phase": ("s32", 8),
                    "personal_event_phase": ("s32", 10),
                    "shop_event_phase": ("s32", 6),
                    "netvs_phase": ("s32", 0),
                    "card_phase": ("s32", 9),
                    "other_phase": ("s32", 9),
                    "local_matching_enable": ("s32", 0),
                    "n_matching_sec": ("s32", 60),
                    "l_matching_sec": ("s32", 60),
                    "is_check_cpu": ("s32", 0),
                    "week_no": ("s32", 0),
                }
            )
            response.content.update(
                {
                    "sel_ranking": array("s16", [-1] * 10),
                    "up_ranking": array("s16", [-1] * 10),
                }
            )
        elif self.spec.version == "v22":
            response.content = {
                "phase": [
                    {"event_id": item("s16", i), "phase": item("s16", p)}
                    for i, p in (
                        (0, 16),
                        (1, 11),
                        (2, 11),
                        (3, 24),
                        (4, 2),
                        (5, 2),
                        (6, 1),
                        (7, 1),
                        (8, 2),
                        (9, 11),
                        (10, 2),
                        (11, 3),
                        (12, 1),
                        (13, 2),
                        (14, 4),
                        (15, 2),
                        (16, 2),
                        (17, 12),
                        (18, 2),
                        (19, 7),
                    )
                ],
                "story": [
                    {
                        "story_id": item("u32", i),
                        "is_limited": item("bool", False),
                        "limit_date": item("u64", 0),
                    }
                    for i in range(173)
                ],
            }
        elif self.spec.version == "v23":
            response.content = {
                "phase": [
                    {"event_id": item("s16", i), "phase": item("s16", p)}
                    for i, p in (
                        (0, 16),
                        (1, 3),
                        (2, 1),
                        (3, 2),
                        (4, 1),
                        (5, 2),
                        (6, 1),
                        (7, 4),
                        (8, 3),
                        (9, 4),
                        (10, 4),
                        (11, 1),
                        (12, 1),
                        (13, 4),
                    )
                ],
                "area": [
                    {
                        "area_id": item("s16", i),
                        "end_date": item("u64", 0),
                        "medal_id": item("s16", i),
                        "is_limit": item("bool", False),
                    }
                    for i in range(1, 101)
                ],
                "goods": self._goods("v23", 420),
            }
        else:
            phases = self._modern_phases()
            response.content = {
                "phase": [
                    {"event_id": item("s16", i), "phase": item("s16", p)}
                    for i, p in phases
                ],
                "choco": [
                    {"choco_id": item("s16", i), "param": item("s32", -1)}
                    for i in range(5)
                ],
                "goods": self._goods(
                    self.spec.version,
                    {"v24": 97, "v25": 133, "v26": 133, "v27": 81}[self.spec.version],
                ),
            }
            if self.spec.version == "v24":
                response.content["area"] = [
                    {
                        "area_id": item("s16", i),
                        "end_date": item("u64", 0),
                        "medal_id": item("s16", i),
                        "is_limit": item("bool", False),
                    }
                    for i in range(16)
                ]

    async def new(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        await self._profile(info, data, response, update_name=True)

    async def conversion(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        await self._profile(info, data, response, update_name=True)

    async def logout(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {}

    async def expire(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {}

    async def update_ranking(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {}

    async def write_course(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {}

    async def read(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        await self._profile(info, data, response, update_name=False)

    async def write(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        if self.spec.version == "v19":
            await self._write_tunestreet(data, response)
            return
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        scores = await self.repo.scores(refid, self.spec.version, force_version=True)
        for stage in elements(data, "stage"):
            music = scalar(field(stage, "no", -1), -1)
            sheet = scalar(field(stage, "sheet", 0), 0)
            if self.spec.version == "v20":
                sheet = {2: 0, 0: 1, 1: 2, 3: 3}.get(sheet, sheet)
            n_data = scalar(field(stage, "n_data", 0), 0)
            clear = N_DATA_CLEAR.get((n_data >> (sheet * 4)) & 0xF, 0)
            self._merge_score(
                scores, music, sheet, scalar(field(stage, "score", 0)), clear
            )
        await self.repo.save_scores(refid, self.spec.version, scores)
        await self._save_extras(refid, data)
        if self.spec.version in ("v22", "v23", "v24", "v25", "v26", "v27"):
            await self._save_achievements(refid, data)
            if self.spec.version == "v24":
                params = await self.repo.params(refid, self.spec.version)
                params.setdefault("params", {})["mission_date"] = (
                    f"{date.today().year}-{date.today().month - 1}-{date.today().day}"  # noqa: DTZ011
                )
                await self.repo.save_params(refid, self.spec.version, params)
        profile = await self.repo.profile(refid)
        response.content = {
            "pref": item("s8", -1),
            "name": item("str", profile.get("name", "ゲスト")),
        }

    async def write_music(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        scores = await self.repo.scores(refid, self.spec.version, force_version=True)
        self._merge_score(
            scores,
            scalar(field(data, "music_num", 0)),
            scalar(field(data, "sheet_num", 0)),
            scalar(field(data, "score", 0)),
            MEDAL_TO_CLEAR.get(scalar(field(data, "clearmedal", 0)), 0),
        )
        await self.repo.save_scores(refid, self.spec.version, scores)

    async def read_score(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        scores = await self.repo.scores(refid, self.spec.version)
        music = []
        for key, value in scores.get("scores", {}).items():
            try:
                music_id, sheet = (int(x) for x in key.split(":", 1))
            except ValueError:
                continue
            if music_id > self.spec.max_music or sheet not in range(4):
                continue
            medal = self._score_medal(value.get("clear_type", 0))
            if self.spec.version in ("v24", "v25", "v26", "v27"):
                music.append(
                    {
                        "music_num": item("s16", music_id),
                        "sheet_num": item("u8", sheet),
                        "score": item("s32", value.get("score", 0)),
                        "clear_type": item("u8", medal),
                        "clear_rank": item("u8", self._rank(value.get("score", 0))),
                        "cnt": item("s16", value.get("cnt", 0)),
                    }
                )
            else:
                music.append(
                    {
                        "music_num": item("s16", music_id),
                        "sheet_num": item("u8", sheet),
                        "score": item("s32", value.get("score", 0)),
                        "clear_type": item("u8", medal),
                        "cnt": item("s16", value.get("cnt", 0)),
                    }
                )
        response.content = {"music": music}

    async def start(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        await self.info(info, data, response)
        response.content["play_id"] = item("s32", 0)

    async def buy(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        item_type = scalar(field(data, "type", -1), -1)
        item_id = scalar(field(data, "id", -1), -1)
        if item_type < 0 or item_id < 0:
            response.status = 1
            return
        lumina = scalar(field(data, "lumina", 0), 0)
        price = scalar(field(data, "price", 0), 0)
        if lumina >= price:
            params = await self.repo.params(refid, self.spec.version)
            params.setdefault("params", {})["player_point"] = lumina - price
            await self.repo.save_params(refid, self.spec.version, params)
            achievements = await self.repo.achievements(
                refid,
                self.spec.version,
                {
                    "collection": "achievements",
                    "version": self.spec.version,
                    "items": {},
                },
            )
            achievements.setdefault("items", {})[f"{item_type}:{item_id}"] = scalar(
                field(data, "param", 0), 0
            )
            await self.repo.save_achievements(refid, self.spec.version, achievements)

    async def friend(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = field(data, "ref_id", "")
        if self.spec.version == "v19" or not refid:
            response.status = 1
            return
        rivals = await self.repo.rivals(refid)
        rival_ids = rivals.get("rivals", [])
        if self.spec.version in ("v20", "v21"):
            friends = []
            for rival in rival_ids[:2]:
                profile = await self.repo.profile(rival)
                scores = await self._scores(rival)
                friend = {
                    "open": item("s8", 1),
                    "g_pm_id": item("str", profile.get("friendId", "000000000000")),
                    "name": item("str", profile.get("name", "ゲスト")),
                    "chara": item("s16", -1),
                    "clear_medal": array("u16", scores["clear_medal"]),
                    "hiscore": item("bin", bytes(scores["hiscore_array"])),
                }
                if self.spec.version == "v21":
                    params = await self.repo.params(rival, self.spec.version)
                    values = params.get("params", {})
                    friend.update(
                        {
                            "hair": item("u8", values.get("hair", 0)),
                            "face": item("u8", values.get("face", 0)),
                            "body": item("u8", values.get("body", 0)),
                            "effect": item("u8", values.get("effect", 0)),
                            "object": item("u8", values.get("object", 0)),
                            "comment": array("u8", values.get("comment", [0, 0])),
                        }
                    )
                friends.append(friend)
            response.content = {"friend": friends}
            return
        rival_index = scalar(field(data, "no", -1), -1)
        if rival_index < 0 or rival_index >= len(rival_ids):
            response.content = {"result": item("s8", 2)}
            return
        friends = []
        for rival in (rival_ids[rival_index],):
            profile = await self.repo.profile(rival)
            params = await self.repo.params(rival, self.spec.version)
            music = []
            for key, score in (
                (await self.repo.scores(rival, self.spec.version))
                .get("scores", {})
                .items()
            ):
                try:
                    music_id, sheet = (int(value) for value in key.split(":", 1))
                except ValueError:
                    continue
                if music_id <= self.spec.max_music and sheet in range(4):
                    clear_medal = CLEAR_TO_MEDAL.get(score.get("clear_type", 0), 0)
                    score_attrs = {
                        "music_num": str(music_id),
                        "sheet_num": str(sheet),
                        "score": str(score.get("score", 0)),
                    }
                    if self.spec.version == "v22":
                        score_attrs["clearmedal"] = str(clear_medal)
                    else:
                        score_attrs["cleartype"] = str(clear_medal)
                        score_attrs["clearrank"] = str(
                            self._rank(score.get("score", 0))
                        )
                    music.append({"@attr": score_attrs})
            friends.append(
                {
                    "no": item("s16", rival_index),
                    "is_open": item("s8", 1),
                    "g_pm_id": item("str", profile.get("friendId", "000000000000")),
                    "name": item("str", profile.get("name", "ゲスト")),
                    "chara": item("s16", params.get("params", {}).get("chara", -1)),
                    "music": music,
                }
            )
        response.content = {"friend": friends}

    def _modern_phases(self) -> list[tuple[int, int]]:
        return list(PHASES["v27"])

    async def _profile(
        self, info: EamuseInfo, data: dict, response: EamuseResponse, update_name: bool
    ) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        profile = await self.repo.profile(refid)
        name = field(data, "name", "")
        if update_name and name:
            profile["name"] = str(name)
            await self.repo.save_profile(refid, profile)
        scores = await self._scores(refid)
        rivals = await self.repo.rivals(refid)
        play_order = sorted(
            scores["play_count"].items(), key=lambda x: x[1], reverse=True
        )
        best = [int(music) for music, _ in play_order[:20]] + [-1] * max(
            0, 20 - len(play_order[:20])
        )
        if self.spec.version in ("v19", "v20", "v21"):
            if self.spec.version == "v19":
                binary_profile, hiscore, town = await self._tunestreet_blobs(
                    refid, profile, await self.repo.params(refid, "v19")
                )
                response.content = {
                    "b": item("bin", binary_profile),
                    "hiscore": item("bin", hiscore),
                    "town": item("bin", town),
                }
                return
            base = {
                "name": item("str", profile.get("name", "ゲスト")),
                "g_pm_id": item("str", profile.get("friendId", "000000000000")),
                "staff": item("s8", 0),
                "is_conv": item("s8", -1),
                "my_best": array("s16", best),
                "clear_medal": array("u16", scores["clear_medal"]),
                "clear_medal_sub": array("u8", [0] * self.spec.max_music),
                "active_fr_num": item("u8", len(rivals.get("rivals", []))),
                "total_play_cnt": item("s32", 100),
                "today_play_cnt": item("s16", 50),
                "consecutive_days": item("s16", 365),
                "latest_music": array("s16", [-1, -1, -1]),
            }
            if self.spec.version == "v21":
                base["collabo"] = item("u8", 255)
            response.content = {
                "base": base,
                "player_card": {"best_music": array("s16", best[:3])},
                "netvs": {
                    "get_ojama": array("s32", [0, 0]),
                    "rank_point": item("s32", 0),
                    "play_point": item("s32", 0),
                    "record": array("s16", [0] * 6),
                    "rank": item("u8", 0),
                    "dialog": [item("str", f"dialog#{i}") for i in range(6)],
                    "ojama_condition": array("s8", [0] * 74),
                    "set_ojama": array("s8", [0, 0, 0]),
                    "set_recommend": array("s8", [0, 0, 0]),
                    "jewelry": array("s8", [0] * 15),
                },
                "hiscore": item("bin", bytes(scores["hiscore_array"])),
            }
            if self.spec.version == "v21":
                response.content.update(
                    {
                        "gakuen_data": {"music_list": item("s32", -1)},
                        "flying_saucer": {
                            "music_list": item("s32", -1),
                            "tune_count": item("s32", -1),
                            "clear_norma": item("u32", 0),
                            "clear_norma_add": item("u32", 0),
                        },
                        "triple_journey": {
                            "music_list": item("s32", -1),
                            "boss_damage": array("s32", [65534] * 4),
                            "boss_stun": array("s32", [0] * 4),
                            "magic_gauge": item("s32", 0),
                            "today_party": item("s32", 0),
                            "union_magic": item("bool", False),
                            "base_attack_rate": item("float", 1.0),
                            "iidx_play_num": item("s32", 0),
                            "reflec_play_num": item("s32", 0),
                            "voltex_play_num": item("s32", 0),
                            "iidx_play_flg": item("bool", True),
                            "reflec_play_flg": item("bool", True),
                            "voltex_play_flg": item("bool", True),
                        },
                        "ios": {
                            "continueRightAnswer": item("s32", 30),
                            "totalRightAnswer": item("s32", 30),
                        },
                        "kac2013": {
                            "music_num": item("s8", 0),
                            "music": item("s16", 0),
                            "sheet": item("u8", 0),
                        },
                        "baseball_data": {"music_list": item("s64", -1)},
                        "floor_infection": [
                            {
                                "infection_id": item("s32", infection),
                                "music_list": item("s32", -1),
                            }
                            for infection in (3, 5, 7)
                        ],
                    }
                )

        else:
            music = []
            for key, score in (
                (await self.repo.scores(refid, self.spec.version))
                .get("scores", {})
                .items()
            ):
                try:
                    music_id, sheet = (int(x) for x in key.split(":", 1))
                except ValueError:
                    continue
                if music_id <= self.spec.max_music and sheet in range(4):
                    music.append(
                        {
                            "music_num": item("s16", music_id),
                            "sheet_num": item("u8", sheet),
                            "cnt": item("s16", score.get("cnt", 0)),
                            "score": item("s32", score.get("score", 0)),
                            "clear_type": item(
                                "u8", CLEAR_TO_MEDAL.get(score.get("clear_type", 0), 0)
                            ),
                            "old_score": item("s32", 0),
                            "old_clear_type": item("u8", 0),
                        }
                    )
            response.content = {
                "result": item("s8", 0),
                "account": {
                    "name": item("str", profile.get("name", "ゲスト")),
                    "g_pm_id": item("str", profile.get("friendId", "000000000000")),
                    "staff": item("s8", 0),
                    "is_conv": item("s8", 0),
                    "item_type": item("s16", 0),
                    "item_id": item("s16", 0),
                    "license_data": array(
                        "s16", [-1] * (20 if self.spec.version != "v22" else 10)
                    ),
                    "active_fr_num": item("u8", len(rivals.get("rivals", []))),
                    "total_play_cnt": item("s16", 100),
                    "today_play_cnt": item("s16", 50),
                    "consecutive_days": item("s16", 365),
                    "total_days": item("s16", 366),
                    "interval_day": item("s16", 1),
                    "latest_music": array("s16", [-1, -1, -1, -1, -1]),
                    "my_best": array("s16", best[:10]),
                },
                "netvs": {
                    "rank_point": item("s32", 0),
                    "record": array("s16", [0] * 6),
                    "rank": item("u8", 0),
                    "vs_rank_old": item("u8", 0),
                    "dialog": [item("str", f"dialog#{i}") for i in range(6)],
                    "ojama_condition": array("s8", [0] * 74),
                    "set_ojama": array("s8", [0, 0, 0]),
                    "set_recommend": array("s8", [0, 0, 0]),
                    "netvs_play_cnt": item("u32", 0),
                },
                "music": music,
                "item": [],
                "achievement": [],
                "chara_param": [],
                "story": [],
            }
            response.content.update(
                {"area": [], "course_data": [], "fes": [], "mission": [], "stamp": []}
            )
            response.content["custom_cate"] = {
                "valid": item("s8", 0),
                "lv_min": item("s8", -1),
                "lv_max": item("s8", -1),
                "medal_min": item("s8", -1),
                "medal_max": item("s8", -1),
                "friend_no": item("s8", -1),
                "score_flg": item("s8", -1),
            }
            if self.spec.version >= "v24":
                response.content["eaappli"] = {"relation": item("s8", -1)}
                response.content["navi_data"] = {
                    "raisePoint": array("s32", [-1, -1, -1, -1, -1]),
                    "navi_param": {
                        "navi_id": item("u16", 0),
                        "friendship": item("s32", 0),
                    },
                }
            if self.spec.version == "v23":
                response.content["account"]["meteor_flg"] = item("bool", True)
                response.content.update(
                    {
                        "gakuen_data": {"music_list": item("s32", -1)},
                        "flying_saucer": {
                            "music_list": item("s32", -1),
                            "tune_count": item("s32", -1),
                            "clear_norma": item("u32", 0),
                            "clear_norma_add": item("u32", 0),
                        },
                        "triple_journey": {
                            "music_list": item("s32", -1),
                            "boss_damage": array("s32", [65534] * 4),
                            "boss_stun": array("s32", [0] * 4),
                            "magic_gauge": item("s32", 0),
                            "today_party": item("s32", 0),
                            "union_magic": item("bool", False),
                            "base_attack_rate": item("float", 1.0),
                            "iidx_play_num": item("s32", 0),
                            "reflec_play_num": item("s32", 0),
                            "voltex_play_num": item("s32", 0),
                            "iidx_play_flg": item("bool", True),
                            "reflec_play_flg": item("bool", True),
                            "voltex_play_flg": item("bool", True),
                        },
                        "ios": {
                            "continueRightAnswer": item("s32", 30),
                            "totalRightAnswer": item("s32", 30),
                        },
                        "kac2013": {
                            "music_num": item("s8", 0),
                            "music": item("s16", 0),
                            "sheet": item("u8", 0),
                        },
                        "baseball_data": {"music_list": item("s64", -1)},
                        "floor_infection": [
                            {
                                "infection_id": item("s32", infection),
                                "music_list": item("s32", -1),
                            }
                            for infection in (3, 5, 7)
                        ],
                    }
                )
        params = await self.repo.params(refid, self.spec.version)
        self._apply_defaults(
            response.content, self.spec.version, params.get("params", {})
        )
        if self.spec.version not in ("v19", "v20", "v21"):
            achievements = await self.repo.achievements(
                refid,
                self.spec.version,
                {"items": {}, "achievements": {}, "stories": {}, "charas": {}},
            )
            self._apply_achievements(response.content, achievements)
            if self.force_unlock:
                response.content.setdefault("item", []).extend(
                    {
                        "type": item("u8", 0),
                        "id": item("u16", music_id),
                        "param": item("u16", 15),
                        "is_new": item("bool", False),
                        "get_time": item("u64", 0),
                    }
                    for music_id in range(1, self.spec.max_music + 1)
                )
            if self.spec.version == "v24":
                mission_date = (
                    f"{date.today().year}-{date.today().month - 1}-{date.today().day}"  # noqa: DTZ011
                )
                params = await self.repo.params(refid, self.spec.version)
                saved_date = params.setdefault("params", {}).setdefault(
                    "mission_date", mission_date
                )
                if saved_date != mission_date:
                    missions = achievements.get("missions", {})
                    next_id = max((int(key) for key in missions), default=0)
                    response.content["mission"] = []
                    for key, value in missions.items():
                        if value.get("mission_comp", 0) == 1:
                            next_id += 1
                            mission_id = next_id
                        else:
                            mission_id = int(key)
                        response.content["mission"].append(
                            {
                                "mission_id": item("u32", mission_id),
                                "gauge_point": item("u32", 0),
                                "mission_comp": item("u32", 0),
                            }
                        )
                else:
                    response.content["mission"] = [
                        {
                            "mission_id": item("u32", mission_id),
                            "gauge_point": item("u32", value.get("gauge_point", 0)),
                            "mission_comp": item("u32", value.get("mission_comp", 0)),
                        }
                        for mission_id, value in achievements.get(
                            "missions", {1: {}, 2: {}, 3: {}}
                        ).items()
                    ]
            if self.spec.version == "v26":
                riddles = achievements.get("riddles", {})
                response.content["riddles_data"] = {
                    "sp_riddles": [
                        {
                            "kaimei_gauge": item("u16", value.get("kaimei_gauge", 0)),
                            "is_cleared": item("bool", value.get("is_cleared", False)),
                            "riddles_cleared": item(
                                "bool", value.get("riddles_cleared", False)
                            ),
                            "select_count": item("u8", value.get("select_count", 0)),
                            "other_count": item("u32", value.get("other_count", 0)),
                        }
                        for value in riddles.values()
                    ],
                    "sh_riddles": [
                        {"sh_riddles_id": item("u32", index)}
                        for index in random.sample(range(1, 21), 3)
                    ],
                }
            if self.spec.version == "v27":
                event = response.content.setdefault("event_p27", {})
                event.setdefault(
                    "first_play", item("bool", not achievements.get("team"))
                )
                event.setdefault(
                    "elem_first_play", item("bool", not achievements.get("battery"))
                )
                event.setdefault("team", [])
                event.setdefault("battery", [])

    @staticmethod
    def _apply_defaults(player: dict, version: str, params: dict) -> None:
        fields = DEFAULT_FIELDS["v24"]
        for name, type_name, path, default, is_array in fields:
            value = params.get(name, params.get(f"{path}.{name}", default))
            target = player
            for part in path.split("."):
                if not isinstance(target, dict):
                    target = None
                    break
                target = target.setdefault(part, {})
            if not isinstance(target, dict):
                continue
            target_name = name.split("__", 1)[0]
            target[target_name] = (
                array(type_name, value) if is_array else item(type_name, value)
            )

    @staticmethod
    def _apply_params(player: dict, params: dict) -> None:
        for path, value in params.items():
            # Older saved documents may use the field name only.  In that case
            # retain it at the root; path-aware documents restore exact nesting.
            parts = path.split(".")
            parent = player
            for part in parts[:-1]:
                if not isinstance(parent, dict):
                    break
                parent = parent.setdefault(part, {})
            else:
                type_name = (
                    "str"
                    if isinstance(value, str)
                    else "bool"
                    if isinstance(value, bool)
                    else "s32"
                )
                if isinstance(value, list):
                    parent[parts[-1]] = array(type_name, value)
                else:
                    parent[parts[-1]] = item(type_name, value)

    @staticmethod
    def _apply_achievements(player: dict, achievements: dict) -> None:
        for key, value in achievements.get("achievements", {}).items():
            player.setdefault("achievement", []).append(
                {"type": item("u8", int(key)), "count": item("u32", value)}
            )
        for key, value in achievements.get("charas", {}).items():
            player.setdefault("chara_param", []).append(
                {"chara_id": item("u16", int(key)), "friendship": item("u16", value)}
            )
        for key, value in achievements.get("stories", {}).items():
            player.setdefault("story", []).append(
                {
                    "story_id": item("u32", int(key)),
                    **{
                        name: item("bool" if name == "is_cleared" else "u32", val)
                        for name, val in value.items()
                    },
                }
            )
        for key, value in achievements.get("items", {}).items():
            try:
                type_id, item_id = (int(x) for x in key.split(":", 1))
            except ValueError:
                continue
            player.setdefault("item", []).append(
                {
                    "type": item("u8", type_id),
                    "id": item("u16", item_id),
                    "param": item("u16", value),
                    "is_new": item("bool", False),
                }
            )
        for key, value in achievements.get("medals", {}).items():
            player.setdefault("medal", []).append(
                {
                    "medal_id": item("s16", int(key)),
                    "level": item("s16", value.get("level", 0)),
                    "exp": item("s32", value.get("exp", 0)),
                    "set_count": item("s32", value.get("set_count", 0)),
                    "get_count": item("s32", value.get("get_count", 0)),
                }
            )
        for key, value in achievements.get("areas", {}).items():
            player.setdefault("area", []).append(
                {
                    "area_id": item("u32", int(key)),
                    "chapter_index": item("u8", value.get("chapter_index", 0)),
                    "gauge_point": item("u16", value.get("gauge_point", 0)),
                    "is_cleared": item("bool", value.get("is_cleared", False)),
                    "diary": item("u32", value.get("diary", 0)),
                }
            )
        for key, value in achievements.get("courses", {}).items():
            player.setdefault("course_data", []).append(
                {
                    "course_id": item("s16", int(key)),
                    "clear_type": item("u8", value.get("clear_type", 0)),
                    "clear_rank": item("u8", value.get("clear_rank", 0)),
                    "total_score": item("s32", value.get("total_score", 0)),
                    "update_count": item("s32", value.get("update_count", 0)),
                    "sheet_num": item("u8", value.get("sheet_num", 0)),
                }
            )
        for key, value in achievements.get("fes", {}).items():
            player.setdefault("fes", []).append(
                {
                    "fes_id": item("u32", int(key)),
                    "chapter_index": item("u8", value.get("chapter_index", 0)),
                    "gauge_point": item("u16", value.get("gauge_point", 0)),
                    "is_cleared": item("bool", value.get("is_cleared", False)),
                }
            )
        for key, value in achievements.get("missions", {}).items():
            player.setdefault("mission", []).append(
                {
                    "mission_id": item("u32", int(key)),
                    "gauge_point": item("u32", value.get("gauge_point", 0)),
                    "mission_comp": item("u32", value.get("mission_comp", 0)),
                }
            )
        for key, value in achievements.get("stamps", {}).items():
            player.setdefault("stamp", []).append(
                {"stamp_id": item("s16", int(key)), "cnt": item("s16", value)}
            )
        if achievements.get("team") or achievements.get("battery"):
            player.setdefault("event_p27", {})["first_play"] = item(
                "bool", not achievements.get("team")
            )
            player["event_p27"]["elem_first_play"] = item(
                "bool", not achievements.get("battery")
            )
            player["event_p27"]["team"] = [
                {
                    "team_id": item("s16", x.get("team_id", 0)),
                    "ex_no": item("s16", x.get("ex_no", 0)),
                    "point": item("u32", x.get("point", 0)),
                    "is_cleared": item("bool", x.get("is_cleared", False)),
                }
                for x in achievements.get("team", [])
            ]
            player["event_p27"]["battery"] = [
                {
                    "battery_id": item("s16", x.get("battery_id", 0)),
                    "energy": item("u32", x.get("energy", 0)),
                    "is_cleared": item("bool", x.get("is_cleared", False)),
                }
                for x in achievements.get("battery", [])
            ]

    async def _scores(self, refid: str) -> dict:
        scores = await self.repo.scores(refid, self.spec.version)
        hiscore = [0] * (((self.spec.max_music * 4) * 17 + 7) // 8)
        medals = [0] * self.spec.max_music
        play_count: dict[int, int] = {}
        for key, value in scores.get("scores", {}).items():
            try:
                music, sheet = (int(x) for x in key.split(":", 1))
            except ValueError:
                continue
            if music > self.spec.max_music or sheet not in range(4):
                continue
            medal = self._score_medal(value.get("clear_type", 0))
            medals[music] |= medal << (sheet * 4)
            index = music * 4 + sheet
            bit = index * 17
            score = int(value.get("score", 0)) << (bit % 8)
            pos = bit // 8
            if pos < len(hiscore):
                hiscore[pos] |= score & 0xFF
            if pos + 1 < len(hiscore):
                hiscore[pos + 1] |= (score >> 8) & 0xFF
            if pos + 2 < len(hiscore):
                hiscore[pos + 2] |= (score >> 16) & 0xFF
            play_count[music] = play_count.get(music, 0) + int(value.get("cnt", 0))
        return {
            "hiscore_array": hiscore,
            "clear_medal": medals,
            "play_count": play_count,
        }

    async def _save_extras(self, refid: str, data: dict) -> None:
        """Persist version fields without losing unknown game extensions.

        Artemis stores these in a versioned ``params`` document. Keeping the
        field path lets later firmware extensions survive a server round trip.
        """
        params = await self.repo.params(refid, self.spec.version)
        values = params.setdefault("params", {})
        allowed = {
            name.split("__", 1)[0] for name, *_ in DEFAULT_FIELDS["v24"]
        }

        def collect(node: Any, path: str = "") -> None:
            if not isinstance(node, dict):
                return
            if "@content" in node and path:
                value = node["@content"]
                if isinstance(value, (str, int, float, bool)) or (
                    isinstance(value, list)
                    and all(isinstance(x, (str, int, float, bool)) for x in value)
                ):
                    key = path.rsplit(".", 1)[-1].split("__", 1)[0]
                    if key not in allowed:
                        return
                    values[key] = (
                        value[0]
                        if isinstance(value, list) and len(value) == 1
                        else value
                    )
            for key, child_node in node.items():
                if not key.startswith("@"):
                    collect(child_node, f"{path}.{key}" if path else key)

        collect(data)
        await self.repo.save_params(refid, self.spec.version, params)

    async def _save_achievements(self, refid: str, data: dict) -> None:
        defaults = {
            "collection": "achievements",
            "version": self.spec.version,
            "achievements": {},
            "stories": {},
            "items": {},
            "charas": {},
            "areas": {},
            "courses": {},
            "fes": {},
            "missions": {},
            "riddles": {},
            "team": [],
            "battery": [],
            "medals": {},
            "stamps": {},
        }
        achievements = await self.repo.achievements(refid, self.spec.version, defaults)
        for node_name, target, fields in (
            ("achievement", "achievements", ("type", "count")),
            (
                "story",
                "stories",
                (
                    "story_id",
                    "chapter_id",
                    "gauge_point",
                    "is_cleared",
                    "clear_chapter",
                ),
            ),
            (
                "area",
                "areas",
                ("area_id", "chapter_index", "gauge_point", "is_cleared", "diary"),
            ),
            (
                "course_data",
                "courses",
                (
                    "course_id",
                    "clear_type",
                    "clear_rank",
                    "total_score",
                    "update_count",
                    "sheet_num",
                ),
            ),
            ("fes", "fes", ("fes_id", "chapter_index", "gauge_point", "is_cleared")),
            ("mission", "missions", ("mission_id", "gauge_point", "mission_comp")),
        ):
            bucket = achievements.setdefault(target, {})
            for node in elements(data, node_name):
                key = scalar(field(node, fields[0]), 0)
                bucket[str(key)] = {
                    name: scalar(field(node, name), 0)
                    if name != "is_cleared"
                    else bool(scalar(field(node, name), 0))
                    for name in fields[1:]
                }
        for node in elements(data, "item"):
            achievements.setdefault("items", {})[
                f"{scalar(field(node, 'type'))}:{scalar(field(node, 'id'))}"
            ] = scalar(field(node, "param"))
        for node in elements(data, "chara_param"):
            achievements.setdefault("charas", {})[
                str(scalar(field(node, "chara_id")))
            ] = scalar(field(node, "friendship"))
        for node in elements(data, "medal"):
            achievements.setdefault("medals", {})[
                str(scalar(field(node, "medal_id")))
            ] = {
                key: scalar(field(node, key))
                for key in ("level", "exp", "set_count", "get_count")
            }
        for node in elements(data, "stamp"):
            achievements.setdefault("stamps", {})[
                str(scalar(field(node, "stamp_id")))
            ] = scalar(field(node, "cnt"))
        riddle_data = child(data, "riddles_data", {})
        for index, node in enumerate(elements(riddle_data, "sp_riddles")):
            achievements.setdefault("riddles", {})[str(index)] = {
                "kaimei_gauge": scalar(field(node, "kaimei_gauge")),
                "is_cleared": bool(scalar(field(node, "is_cleared"))),
                "riddles_cleared": bool(scalar(field(node, "riddles_cleared"))),
                "select_count": scalar(field(node, "select_count")),
                "other_count": scalar(field(node, "other_count")),
            }
        event = child(data, "event_p27", {})
        for node in elements(event, "team"):
            value = {
                "team_id": scalar(field(node, "team_id")),
                "ex_no": scalar(field(node, "ex_no")),
                "point": scalar(field(node, "point")),
                "is_cleared": bool(scalar(field(node, "is_cleared"))),
            }
            teams = achievements.setdefault("team", [])
            existing = next(
                (x for x in teams if x.get("team_id") == value["team_id"]), None
            )
            if existing is None:
                teams.append(value)
            else:
                existing.update(value)
        for node in elements(event, "battery"):
            value = {
                "battery_id": scalar(field(node, "battery_id")),
                "energy": scalar(field(node, "energy")),
                "is_cleared": bool(scalar(field(node, "is_cleared"))),
            }
            batteries = achievements.setdefault("battery", [])
            existing = next(
                (x for x in batteries if x.get("battery_id") == value["battery_id"]),
                None,
            )
            if existing is None:
                batteries.append(value)
            else:
                existing.update(value)
        await self.repo.save_achievements(refid, self.spec.version, achievements)

    @staticmethod
    def _rank(score: Any) -> int:
        score = scalar(score)
        for limit, rank in (
            (50000, 1),
            (62000, 2),
            (72000, 3),
            (82000, 4),
            (90000, 5),
            (95000, 6),
            (98000, 7),
        ):
            if score < limit:
                return rank
        return 8

    def _score_medal(self, clear_type: Any) -> int:
        if self.spec.version in ("v20", "v21"):
            return {
                100: 1,
                200: 2,
                300: 3,
                400: 5,
                500: 5,
                600: 6,
                700: 7,
                800: 9,
                900: 10,
                1000: 11,
                1100: 15,
            }.get(clear_type, 0)
        return CLEAR_TO_MEDAL.get(clear_type, 0)

    @staticmethod
    def _merge_score(
        scores: dict, music: int, sheet: int, score: int, clear_type: int
    ) -> None:
        key = f"{music}:{sheet}"
        old = scores.setdefault("scores", {}).get(key)
        if old is None:
            scores["scores"][key] = {"score": score, "cnt": 1, "clear_type": clear_type}
        else:
            old.update(
                score=max(score, old.get("score", 0)),
                cnt=old.get("cnt", 0) + 1,
                clear_type=max(clear_type, old.get("clear_type", 0)),
            )

    @staticmethod
    def _items(values: dict[str, tuple[str, Any]]) -> dict:
        return {
            key: item(type_name, value) for key, (type_name, value) in values.items()
        }

    @staticmethod
    def _goods(version: str, count: int) -> list[dict]:
        result = []
        for index in range(count):
            if version == "v23":
                number = index + 1
                if number <= 80:
                    price = 60
                elif number <= 120:
                    price = 250
                elif number <= 142:
                    price = 500
                elif number <= 300:
                    price = 100
                else:
                    price = 150
                result.append(
                    {
                        "goods_id": item("s16", number),
                        "price": item("s32", price),
                        "goods_type": item("s16", 0),
                    }
                )
                continue
            if index < 15:
                price = 30
            elif index < 30:
                price = 40
            elif index < 45:
                price = 60
            elif index < 60:
                price = 80
            else:
                price = 200
            result.append(
                {
                    "item_id": item("s32", index + 1),
                    "item_type": item("s16", 3),
                    "price": item("s32", price),
                    "goods_type": item("s16", 0),
                }
            )
        return result


class PopnRoutes:
    """Pop'n Music 19 through Unilab route set.

    The old games use ``K39/L39/M39`` with the playerdata module.  Later games
    expose their version in the module name (player22/player23/player24), as
    in the corresponding Pop'n protocol revisions.
    """

    # Only the current Pop'n Hi Cheers cabinet is in scope.
    game_codes = ("M39",)

    @staticmethod
    def service_modules(game_code: str, model: str = "") -> tuple[str, ...]:
        """Return the title modules advertised by ``services.get``.

        Asphyxia's Pop'n plugin adds these modules dynamically during service
        discovery.  The native adapter has no external plugin loader, so it
        must expose the equivalent list itself.
        """
        return ("local2", "lobby2")

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.cfg = cfg
        self.data = Data(cfg)
        self._handlers = {
            "v27": PopnVersionHandler(
                PopnRepository(self.data, "M39"),
                SPECS["v27"],
                cfg.konami.popn_force_unlock,
            ),
        }

    def register(self, router: EamuseRouter) -> None:
        code = "M39"
        methods = (
            "new", "read", "start", "write", "friend", "write_music",
            "write_course", "update_ranking", "buy", "read_score", "logout",
        )
        for method in methods:
            router.add(code, "player24", method, self._modern("v24", method))
            router.add(code, "player", method, self._modern_player("v24", method))
        for method in ("end", "tsumtsum", "read_option"):
            router.add(code, "player", method, self.legacy_event)
        for method in ("boot", "error", "dlstatus", "write"):
            router.add(code, "pcb", method, self.legacy_event)
        router.add(code, "info", "common", self._modern("v24", "info"))
        router.add(code, "info24", "common", self._modern("v24", "info"))
        router.add(code, "loctest24", "log", self.legacy_event)
        router.add(code, "lobby24", "getList", self.legacy_event)
        router.webui(code, self.webui_event)

    async def webui_event(self, name: str, data: dict) -> None:
        """Handle Pop'n profile, rival, and unlock WebUI events."""
        repository = self._handlers["v27"].repo
        if name == "updatePnmPlayerInfo":
            await repository.update_profile_name(
                str(data.get("refid", "")), str(data.get("name", ""))
            )
        elif name == "addRival":
            await repository.add_rival(
                str(data.get("refid", "")), str(data.get("rivalid", ""))
            )
        elif name == "deleteRival":
            await repository.delete_rival(
                str(data.get("refid", "")), str(data.get("rivalid", ""))
            )
    def _modern(self, version: str, name: str):
        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            await getattr(self._handlers["v27"], name)(info, data, response)

        return handler

    def _modern_player(self, version: str, name: str):
        """Serve the native M39 ``player`` alias with its legacy base node."""
        modern = self._modern(version, name)

        async def handler(info: EamuseInfo, data: dict, response: EamuseResponse):
            await modern(info, data, response)
            account = response.content.get("account")
            if isinstance(account, dict):
                response.content.setdefault("base", account)

        return handler

    async def legacy_event(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {}
