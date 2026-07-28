"""Version-specific Pop'n protocol handlers.

The wire fields here follow the handlers in plugins-main/popn@asphyxia.  The
repository is intentionally shared by all versions, matching Asphyxia's
profile/params/scores/achievements collections.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import random
from typing import Any

from core.konami.protocol import EamuseInfo, EamuseResponse

from .defaults import DEFAULT_FIELDS
from .helpers import array, attr, child, content, item, scalar
from .repository import PopnRepository


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
    "v19": VersionSpec("v19", 1047),
    "v20": VersionSpec("v20", 1150),
    "v21": VersionSpec("v21", 1350),
    "v22": VersionSpec("v22", 1422),
    "v23": VersionSpec("v23", 1550),
    "v24": VersionSpec("v24", 1704),
    "v25": VersionSpec("v25", 1877),
    "v26": VersionSpec("v26", 2019),
    "v27": VersionSpec("v27", 2188),
}

EXTRA_V26 = {
    "card_again_count",
    "sp_riddles_id",
    "point",
    "step",
    "quest_point",
    "step_nos",
    "quest_point_nos",
}
EXTRA_V27 = {"lift", "lift_rate", "team_id", "select_battery_id", "today_first_play"}
PHASES = {
    "v24": [
        (0, 11),
        (1, 2),
        (2, 2),
        (3, 4),
        (4, 1),
        (5, 0),
        (6, 1),
        (7, 1),
        (8, 2),
        (9, 2),
        (10, 15),
        (11, 1),
        (12, 2),
        (13, 1),
    ],
    "v25": [
        (0, 23),
        (1, 4),
        (10, 30),
        (14, 39),
        (15, 2),
        (16, 3),
        (17, 8),
        (18, 1),
        (19, 1),
        (20, 13),
        (21, 20),
        (22, 2),
        (23, 1),
        (24, 1),
    ],
    "v26": [(0, 30), (25, 62), (26, 3), (27, 2), (28, 2), (29, 5), (30, 6)],
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
        scores = await self.repo.scores(refid, self.spec.version)
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
                    f"{date.today().year}-{date.today().month - 1}-{date.today().day}"
                )
                await self.repo.save_params(refid, self.spec.version, params)
        profile = await self.repo.profile(refid)
        response.content = {
            "pref": item("s8", -1),
            "name": item("str", profile.get("name", "ゲスト")),
        }

    async def town(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        profile = await self.repo.profile(refid)
        params = await self.repo.params(refid, "v19")
        achievements = await self.repo.achievements(
            refid,
            "v19",
            {
                "apply": [""] * 6,
                "building": [[0] * 8 for _ in range(8)],
                "base": [0] * 4,
            },
        )
        town = bytearray(180)
        chara = scalar(params.get("params", {}).get("chara", 0), 0)
        town[0:2] = chara.to_bytes(2, "little", signed=False)
        for row in range(8):
            for column in range(8):
                town[42 + row * 8 + column] = (
                    scalar(achievements.get("building", [[0] * 8] * 8)[row][column], 0)
                    & 0xFF
                )
        friend_id = str(profile.get("friendId", ""))[:12].encode("ascii", "replace")
        town[106 : 106 + len(friend_id)] = friend_id
        name = str(profile.get("name", "ゲスト")).encode("shift_jis", "replace")[:12]
        town[119 : 119 + len(name)] = name
        for index, value in enumerate(achievements.get("base", [0] * 4)[:4]):
            town[173 + index] = scalar(value, 0) & 0xFF
        response.content = {
            "residence": {"@attr": {"id": "0"}},
            "map": [
                item("bin", bytes(town), residence="0"),
            ],
        }

    async def _write_tunestreet(self, data: dict, response: EamuseResponse) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        params = await self.repo.params(refid, "v19")
        saved = params.setdefault("params", {})
        for name in (
            "tp",
            "play_mode",
            "chara_num",
            "option",
            "last_play_flag",
            "medal_and_friend",
            "music_num",
            "sheet_num",
            "category_num",
            "skin_sd_bgm",
            "skin_sd_se",
            "skin_tex_cmn",
            "skin_tex_note",
        ):
            value = field(data, name, None)
            if value is not None:
                saved[name] = scalar(value, 0)
        await self.repo.save_params(refid, "v19", params)
        scores = await self.repo.scores(refid, "v19")
        for music_node in elements(data, "music"):
            music = scalar(field(music_node, "music_num", 0), 0)
            sheet = scalar(field(music_node, "sheet_num", 0), 0)
            score = scalar(field(music_node, "score", 0), 0)
            packed = scalar(field(music_node, "data", 0), 0)
            if music > self.spec.max_music or sheet in (4, 5):
                continue
            play_mode = saved.get("play_mode", 0)
            if play_mode == 4:
                if sheet in (2, 6, 7):
                    continue
                sheet = {0: 1, 1: 2, 3: 3}.get(sheet, sheet)
            else:
                sheet = {0: 4, 1: 5, 2: 9, 3: 6, 6: 7, 7: 8}.get(sheet, sheet)
            shift = {9: 4, 4: 0, 5: 2, 6: 6, 1: 0, 2: 2, 3: 6, 7: 9, 8: 8}.get(sheet, 0)
            mask = 0x1 if sheet in (7, 8) else 0x3
            flags = (packed >> shift) & mask
            clear_type = {0: 100, 1: 500, 2: 800, 3: 1100}.get(flags, 100)
            self._merge_score(scores, music, sheet, score, clear_type)
        await self.repo.save_scores(refid, "v19", scores)
        town = child(data, "town", {})
        if isinstance(town, dict):
            achievements = await self.repo.achievements(
                refid,
                "v19",
                {
                    "collection": "achievements",
                    "version": "v19",
                    "apply": [""] * 6,
                    "bought_flg": [0] * 3,
                    "build_flg": [0] * 8,
                    "chara_flg": [0] * 19,
                    "event_flg": [0] * 4,
                    "base": [0] * 4,
                    "building": [[0] * 8 for _ in range(8)],
                    "play_type": 0,
                },
            )
            town_attrs = town.get("@attr", {})
            for index in range(6):
                achievements.setdefault("apply", [""] * 6)[index] = town_attrs.get(
                    f"apply_gpmid_{index}", ""
                )
            for key, count in (
                ("bought_flg", 3),
                ("build_flg", 8),
                ("chara_flg", 19),
                ("event_flg", 4),
                ("base", 4),
            ):
                raw = town_attrs.get(key)
                if raw is not None:
                    achievements[key] = [scalar(x, 0) for x in str(raw).split(",")][
                        :count
                    ]
                    achievements[key] += [0] * (count - len(achievements[key]))
            for index in range(8):
                raw = town_attrs.get(f"building_{index}")
                if raw is not None:
                    values = [scalar(x, 0) for x in str(raw).split(",")][:8]
                    achievements.setdefault("building", [[0] * 8 for _ in range(8)])[
                        index
                    ] = values + [0] * (8 - len(values))
            achievements["play_type"] = scalar(town_attrs.get("play_type", 0), 0)
            await self.repo.save_achievements(refid, "v19", achievements)
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
        scores = await self.repo.scores(refid, self.spec.version)
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
            medal = CLEAR_TO_MEDAL.get(value.get("clear_type", 0), 0)
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
        response.content["play_id"] = item("s32", 1)

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
        rivals = await self.repo.rivals(refid)
        rival_index = scalar(field(data, "no", -1), -1)
        rival_ids = rivals.get("rivals", [])
        if rival_index < 0 or rival_index >= len(rival_ids):
            response.content = {"result": item("s8", 2)}
            return
        friends = []
        for rival in (rival_ids[rival_index],):
            profile = await self.repo.profile(rival)
            friends.append(
                {
                    "no": item("s16", rival_index),
                    "is_open": item("s8", 1),
                    "g_pm_id": item("str", profile.get("friendId", "000000000000")),
                    "name": item("str", profile.get("name", "ゲスト")),
                    "chara": item("s16", -1),
                    "clear_medal": array(
                        "u16", (await self._scores(rival))["clear_medal"]
                    ),
                    "hiscore": item(
                        "bin", bytes((await self._scores(rival))["hiscore_array"])
                    ),
                }
            )
        response.content = {"friend": friends}

    def _modern_phases(self) -> list[tuple[int, int]]:
        if self.spec.version == "v24":
            return list(PHASES["v24"])
        if self.spec.version == "v25":
            return list(dict.fromkeys(PHASES["v24"] + PHASES["v25"]))
        if self.spec.version == "v26":
            return list(dict.fromkeys(PHASES["v24"] + PHASES["v25"] + PHASES["v26"]))
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
                    f"{date.today().year}-{date.today().month - 1}-{date.today().day}"
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

    async def _tunestreet_blobs(
        self, refid: str, profile: dict, params_document: dict
    ) -> tuple[bytes, bytes, bytes]:
        params = params_document.get("params", {})
        achievements = await self.repo.achievements(
            refid,
            "v19",
            {
                "apply": [""] * 6,
                "building": [[0] * 8 for _ in range(8)],
                "base": [0] * 4,
            },
        )
        binary = bytearray(2892)
        name = str(profile.get("name", "ゲスト")).encode("shift_jis", "replace")[:12]
        binary[: len(name)] = name
        friend = str(profile.get("friendId", "000000000000")).encode(
            "ascii", "replace"
        )[:12]
        binary[17 : 17 + len(friend)] = friend
        for offset, key, width in (
            (38, "skin_tex_note", 1),
            (39, "skin_tex_cmn", 1),
            (40, "skin_sd_bgm", 1),
            (41, "skin_sd_se", 1),
            (44, "option", 4),
            (60, "chara", 2),
            (62, "music", 2),
            (64, "sheet", 1),
            (65, "category", 1),
        ):
            value = scalar(params.get(key, 0), 0)
            binary[offset : offset + width] = value.to_bytes(
                width, "little", signed=False
            )
        mode = scalar(params.get("play_mode", 0), 0)
        binary[13] = {2: 1, 3: 1, 4: 5, 5: 2, 6: 4}.get(mode, 0)
        binary[14] = {0: 1, 2: 1, 4: 255, 5: 255, 6: 255}.get(mode, 0)
        binary[15] = scalar(params.get("last_play_flag", 0), 0) & 0xFF
        binary[16] = scalar(params.get("medal_and_friend", 0), 0) & 0xFF
        scores = (await self.repo.scores(refid, "v19")).get("scores", {})
        hiscore = bytearray(((self.spec.max_music * 7 * 17) + 7) // 8)
        play_count: dict[int, int] = {}
        slots = {9: 0, 4: 1, 5: 2, 6: 3, 1: 4, 2: 5, 3: 6}
        shifts = {9: 4, 4: 0, 5: 2, 6: 6, 1: 0, 2: 2, 3: 6, 7: 9, 8: 8}
        played = {
            9: 0x2000,
            4: 0x0800,
            5: 0x1000,
            6: 0x4000,
            1: 0x0800,
            2: 0x1000,
            3: 0x4000,
            7: 0,
            8: 0,
        }
        flag_values = {
            100: 0,
            200: 0,
            300: 0,
            400: 1,
            500: 1,
            600: 1,
            700: 1,
            800: 2,
            900: 2,
            1000: 2,
            1100: 3,
        }
        for key, score_data in scores.items():
            try:
                music, sheet = (int(value) for value in key.split(":", 1))
            except (TypeError, ValueError):
                continue
            if music > self.spec.max_music or sheet == 0:
                continue
            flags = flag_values.get(int(score_data.get("clear_type", 100)), 0)
            packed = (flags << shifts.get(sheet, 0)) | played.get(sheet, 0)
            pos = 108 + music * 2
            if pos + 1 < len(binary):
                binary[pos] |= packed & 0xFF
                binary[pos + 1] |= packed >> 8
            slot = slots.get(sheet)
            if slot is None:
                continue
            bit = (music * 7 + slot) * 17
            pos = bit // 8
            packed_score = int(score_data.get("score", 0)) << (bit % 8)
            if pos + 2 < len(hiscore):
                hiscore[pos] |= packed_score & 0xFF
                hiscore[pos + 1] |= packed_score >> 8
                hiscore[pos + 2] |= packed_score >> 16
            play_count[music] = play_count.get(music, 0) + int(score_data.get("cnt", 0))
        for index, music in enumerate(
            sorted(play_count, key=play_count.get, reverse=True)[:20]
        ):
            binary[68 + index * 2 : 70 + index * 2] = int(music).to_bytes(2, "little")
        town = bytearray(272)
        town[0:4] = scalar(params.get("tp", 100), 100).to_bytes(
            4, "little", signed=False
        )
        for key, offset, count in (
            ("bought_flg", 4, 3),
            ("build_flg", 16, 8),
            ("chara_flg", 48, 19),
            ("event_flg", 124, 4),
        ):
            for index, value in enumerate(achievements.get(key, [])[:count]):
                town[offset + index * 4 : offset + index * 4 + 4] = scalar(
                    value, 0
                ).to_bytes(4, "little", signed=False)
        town[140] = scalar(achievements.get("play_type", 0), 0) & 0xFF
        for index, value in enumerate(achievements.get("apply", [])[:6]):
            encoded = str(value).encode("shift_jis", "replace")[:12]
            town[141 + index * 13 : 141 + index * 13 + len(encoded)] = encoded
        return bytes(binary), bytes(hiscore), bytes(town)

    @staticmethod
    def _apply_defaults(player: dict, version: str, params: dict) -> None:
        fields = (
            DEFAULT_FIELDS.get("v24", [])
            if version in ("v24", "v25", "v26", "v27")
            else DEFAULT_FIELDS.get(version, [])
        )
        for name, type_name, path, default, is_array in fields:
            if version in ("v24", "v25") and name in EXTRA_V26 | EXTRA_V27:
                continue
            if version == "v26" and name in EXTRA_V27:
                continue
            value = params.get(name, params.get(f"{path}.{name}", default))
            target = player
            for part in path.split("."):
                target = target.setdefault(part, {})
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
            medal = CLEAR_TO_MEDAL.get(value.get("clear_type", 0), 0)
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

        Asphyxia stores these in a versioned ``params`` document.  Keeping the
        field path lets later firmware extensions survive a server round trip.
        """
        params = await self.repo.params(refid, self.spec.version)
        values = params.setdefault("params", {})

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
            "battery": {},
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
