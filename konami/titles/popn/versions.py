"""Version-specific Pop'n protocol handlers.

The wire fields here follow the handlers in plugins-main/popn@asphyxia.  The
repository is intentionally shared by all versions, matching Asphyxia's
profile/params/scores/achievements collections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.konami.protocol import EamuseInfo, EamuseResponse

from .defaults import DEFAULT_FIELDS
from .helpers import array, attr, child, content, item, scalar, walk_get, walk_set
from .repository import PopnRepository


CLEAR_TO_MEDAL = {100: 1, 200: 2, 300: 3, 400: 4, 500: 5, 600: 6, 700: 7, 800: 8, 900: 9, 1000: 10, 1100: 11}
MEDAL_TO_CLEAR = {value: key for key, value in CLEAR_TO_MEDAL.items()}
N_DATA_CLEAR = {1: 100, 2: 200, 3: 300, 5: 500, 6: 600, 7: 700, 9: 800, 10: 900, 11: 1000, 15: 1100}


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

EXTRA_V26 = {"card_again_count", "sp_riddles_id", "point", "step", "quest_point", "step_nos", "quest_point_nos"}
EXTRA_V27 = {"lift", "lift_rate", "team_id", "select_battery_id", "today_first_play"}
PHASES = {
    "v24": [(0,11),(1,2),(2,2),(3,4),(4,1),(5,0),(6,1),(7,1),(8,2),(9,2),(10,15),(11,1),(12,2),(13,1)],
    "v25": [(0,23),(1,4),(10,30),(14,39),(15,2),(16,3),(17,8),(18,1),(19,1),(20,13),(21,20),(22,2),(23,1),(24,1)],
    "v26": [(0,30),(25,62),(26,3),(27,2),(28,2),(29,5),(30,6)],
    "v27": [(0,6),(1,6),(2,4),(3,0),(4,7),(5,48),(6,2),(7,6),(8,2),(9,44),(10,1),(11,2),(12,2),(13,2)],
}


class PopnVersionHandler:
    def __init__(self, repository: PopnRepository, spec: VersionSpec, force_unlock: bool = True) -> None:
        self.repo = repository
        self.spec = spec
        self.force_unlock = force_unlock

    async def info(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        if self.spec.version == "v19":
            response.content = {"@attr": {"game_phase": "2", "ir_phase": "14", "event_phase": "15", "netvs_phase": "18", "card_phase": "3", "gfdm_phase": "2", "jubeat_phase": "2", "local_matching_enable": "0", "matching_sec": "120", "boss_diff": ",".join(["100"] * 10), "boss_battle_point": "1"}}
        elif self.spec.version == "v20":
            response.content = self._items({
                "game_phase": ("s32", 2), "ir_phase": ("s32", 0), "event_phase": ("s32", 5), "netvs_phase": ("s32", 0),
                "card_phase": ("s32", 6), "illust_phase": ("s32", 2), "psp_phase": ("s32", 5), "other_phase": ("s32", 1),
                "jubeat_phase": ("s32", 1), "public_phase": ("s32", 3), "kac_phase": ("s32", 2), "local_matching": ("s32", 0),
                "n_matching_sec": ("s32", 60), "l_matching_sec": ("s32", 60), "is_check_cpu": ("s32", 0), "week_no": ("s32", 0),
            })
            response.content.update({"ng_illust": array("s32", [0] * 10), "sel_ranking": array("s16", [-1] * 10), "up_ranking": array("s16", [-1] * 10)})
        elif self.spec.version == "v21":
            response.content = self._items({
                "ir_phase": ("s32", 0), "music_open_phase": ("s32", 8), "collabo_phase": ("s32", 8), "personal_event_phase": ("s32", 10),
                "shop_event_phase": ("s32", 6), "netvs_phase": ("s32", 0), "card_phase": ("s32", 9), "other_phase": ("s32", 9),
                "local_matching_enable": ("s32", 0), "n_matching_sec": ("s32", 60), "l_matching_sec": ("s32", 60), "is_check_cpu": ("s32", 0), "week_no": ("s32", 0),
            })
            response.content.update({"sel_ranking": array("s16", [-1] * 10), "up_ranking": array("s16", [-1] * 10)})
        elif self.spec.version == "v22":
            response.content = {"phase": [ {"event_id": item("s16", i), "phase": item("s16", p)} for i, p in ((0,16),(1,11),(2,11),(3,24),(4,2),(5,2),(6,1),(7,1),(8,2),(9,11),(10,2),(11,3),(12,1),(13,2),(14,4),(15,2),(16,2),(17,12),(18,2),(19,7)) ], "story": [{"story_id": item("u32", i), "is_limited": item("bool", False), "limit_date": item("u64", 0)} for i in range(173)]}
        elif self.spec.version == "v23":
            response.content = {"phase": [{"event_id": item("s16", i), "phase": item("s16", p)} for i, p in ((0,16),(1,3),(2,1),(3,2),(4,1),(5,2),(6,1),(7,4),(8,3),(9,4),(10,4),(11,1),(12,1),(13,4))], "area": [{"area_id": item("s16", i), "end_date": item("u64", 0), "medal_id": item("s16", i), "is_limit": item("bool", False)} for i in range(1, 101)], "goods": self._goods(420)}
        else:
            response.content = {"phase": [{"event_id": item("s16", i), "phase": item("s16", p)} for i, p in PHASES[self.spec.version]], "choco": [{"choco_id": item("s16", i), "param": item("s32", -1)} for i in range(5)], "goods": self._goods({"v24":97,"v25":133,"v26":133,"v27":81}[self.spec.version])}

    async def new(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        await self._profile(info, data, response, update_name=True)

    async def read(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        await self._profile(info, data, response, update_name=False)

    async def write(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        scores = await self.repo.scores(refid, self.spec.version)
        for stage in elements(data, "stage"):
            music = scalar(field(stage, "no", -1), -1)
            sheet = scalar(field(stage, "sheet", 0), 0)
            n_data = scalar(field(stage, "n_data", 0), 0)
            clear = N_DATA_CLEAR.get((n_data >> (sheet * 4)) & 0xF, 0)
            self._merge_score(scores, music, sheet, scalar(field(stage, "score", 0)), clear)
        await self.repo.save_scores(refid, self.spec.version, scores)
        await self._save_extras(refid, data)
        if self.spec.version in ("v22", "v23", "v24", "v25", "v26", "v27"):
            await self._save_achievements(refid, data)
        profile = await self.repo.profile(refid)
        response.content = {"pref": item("s8", -1), "name": item("str", profile.get("name", "ゲスト"))}

    async def write_music(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        refid = field(data, "ref_id", "")
        if not refid:
            response.status = 1
            return
        scores = await self.repo.scores(refid, self.spec.version)
        self._merge_score(scores, scalar(field(data, "music_num", 0)), scalar(field(data, "sheet_num", 0)), scalar(field(data, "score", 0)), MEDAL_TO_CLEAR.get(scalar(field(data, "clearmedal", 0)), 0))
        await self.repo.save_scores(refid, self.spec.version, scores)

    async def read_score(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
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
                music.append({"music_num": item("s16", music_id), "sheet_num": item("u8", sheet), "score": item("s32", value.get("score", 0)), "clear_type": item("u8", medal), "clear_rank": item("u8", self._rank(value.get("score", 0))), "cnt": item("s16", value.get("cnt", 0))})
            else:
                music.append({"music_num": item("s16", music_id), "sheet_num": item("u8", sheet), "score": item("s32", value.get("score", 0)), "clear_type": item("u8", medal), "cnt": item("s16", value.get("cnt", 0))})
        response.content = {"music": music}

    async def start(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        response.content = {"result": item("s8", 0)}

    async def buy(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        response.content = {"result": item("s8", 0)}

    async def friend(self, info: EamuseInfo, data: dict, response: EamuseResponse) -> None:
        refid = field(data, "ref_id", "")
        rivals = await self.repo.rivals(refid)
        friends = []
        for rival in rivals.get("rivals", [])[:2]:
            profile = await self.repo.profile(rival)
            friends.append({"open": item("s8", 1), "g_pm_id": item("str", profile.get("friendId", "000000000000")), "name": item("str", profile.get("name", "ゲスト")), "chara": item("s16", -1), "clear_medal": array("u16", (await self._scores(rival))["clear_medal"]), "hiscore": item("bin", bytes((await self._scores(rival))["hiscore_array"]))})
        response.content = {"friend": friends}

    async def _profile(self, info: EamuseInfo, data: dict, response: EamuseResponse, update_name: bool) -> None:
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
        play_order = sorted(scores["play_count"].items(), key=lambda x: x[1], reverse=True)
        best = [int(music) for music, _ in play_order[:20]] + [-1] * max(0, 20 - len(play_order[:20]))
        if self.spec.version in ("v19", "v20", "v21"):
            base = {"name": item("str", profile.get("name", "ゲスト")), "g_pm_id": item("str", profile.get("friendId", "000000000000")), "staff": item("s8", 0), "is_conv": item("s8", -1), "my_best": array("s16", best), "clear_medal": array("u16", scores["clear_medal"]), "clear_medal_sub": array("u8", [0] * self.spec.max_music), "active_fr_num": item("u8", len(rivals.get("rivals", []))), "total_play_cnt": item("s32", 100), "today_play_cnt": item("s16", 50), "consecutive_days": item("s16", 365), "latest_music": array("s16", [-1,-1,-1])}
            response.content = {"base": base, "player_card": {"best_music": array("s16", best[:3])}, "netvs": {"get_ojama": array("s32", [0,0]), "rank_point": item("s32", 0), "play_point": item("s32", 0), "record": array("s16", [0]*6), "rank": item("u8", 0), "dialog": [item("str", f"dialog#{i}") for i in range(6)], "ojama_condition": array("s8", [0]*74), "set_ojama": array("s8", [0,0,0]), "set_recommend": array("s8", [0,0,0]), "jewelry": array("s8", [0]*15)}, "hiscore": item("bin", bytes(scores["hiscore_array"]))}
        else:
            music = []
            for key, score in (await self.repo.scores(refid, self.spec.version)).get("scores", {}).items():
                try: music_id, sheet = (int(x) for x in key.split(":", 1))
                except ValueError: continue
                if music_id <= self.spec.max_music and sheet in range(4):
                    music.append({"music_num": item("s16", music_id), "sheet_num": item("u8", sheet), "cnt": item("s16", score.get("cnt", 0)), "score": item("s32", score.get("score", 0)), "clear_type": item("u8", CLEAR_TO_MEDAL.get(score.get("clear_type", 0), 0)), "old_score": item("s32", 0), "old_clear_type": item("u8", 0)})
            response.content = {"result": item("s8", 0), "account": {"name": item("str", profile.get("name", "ゲスト")), "g_pm_id": item("str", profile.get("friendId", "000000000000")), "staff": item("s8", 0), "is_conv": item("s8", 0), "item_type": item("s16", 0), "item_id": item("s16", 0), "license_data": array("s16", [-1]*10), "active_fr_num": item("u8", len(rivals.get("rivals", []))), "my_best": array("s16", best[:10])}, "netvs": {"rank_point": item("s32", 0), "record": array("s16", [0]*6), "rank": item("u8", 0), "vs_rank_old": item("u8", 0), "dialog": [item("str", f"dialog#{i}") for i in range(6)], "ojama_condition": array("s8", [0]*74), "set_ojama": array("s8", [0,0,0]), "set_recommend": array("s8", [0,0,0]), "netvs_play_cnt": item("u32", 0)}, "music": music, "item": [], "achievement": [], "chara_param": [], "story": []}
            response.content.update({"area": [], "course_data": [], "fes": [], "mission": [], "stamp": []})
        params = await self.repo.params(refid, self.spec.version)
        self._apply_defaults(response.content, self.spec.version, params.get("params", {}))
        if self.spec.version not in ("v19", "v20", "v21"):
            achievements = await self.repo.achievements(refid, self.spec.version, {"items": {}, "achievements": {}, "stories": {}, "charas": {}})
            self._apply_achievements(response.content, achievements)
            if self.force_unlock:
                response.content.setdefault("item", []).extend({"type": item("u8", 0), "id": item("u16", music_id), "param": item("u16", 15), "is_new": item("bool", False), "get_time": item("u64", 0)} for music_id in range(1, self.spec.max_music + 1))
            if self.spec.version == "v24" and not response.content.get("mission"):
                response.content["mission"] = [{"mission_id": item("u32", mission_id), "gauge_point": item("u32", 0), "mission_comp": item("u32", 0)} for mission_id in (1, 2, 3)]
            if self.spec.version == "v26":
                riddles = achievements.get("riddles", {})
                response.content["riddles_data"] = {"sp_riddles": [{"kaimei_gauge": item("u16", value.get("kaimei_gauge", 0)), "is_cleared": item("bool", value.get("is_cleared", False)), "riddles_cleared": item("bool", value.get("riddles_cleared", False)), "select_count": item("u8", value.get("select_count", 0)), "other_count": item("u32", value.get("other_count", 0))} for value in riddles.values()], "sh_riddles": [{"sh_riddles_id": item("u32", index)} for index in (1, 2, 3)]}
            if self.spec.version == "v27":
                event = response.content.setdefault("event_p27", {})
                event.setdefault("first_play", item("bool", not achievements.get("team")))
                event.setdefault("elem_first_play", item("bool", not achievements.get("battery")))
                event.setdefault("team", [])
                event.setdefault("battery", [])

    @staticmethod
    def _apply_defaults(player: dict, version: str, params: dict) -> None:
        fields = DEFAULT_FIELDS.get("v24", []) if version in ("v24", "v25", "v26", "v27") else DEFAULT_FIELDS.get(version, [])
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
            target[target_name] = array(type_name, value) if is_array else item(type_name, value)

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
                type_name = "str" if isinstance(value, str) else "bool" if isinstance(value, bool) else "s32"
                if isinstance(value, list):
                    parent[parts[-1]] = array(type_name, value)
                else:
                    parent[parts[-1]] = item(type_name, value)

    @staticmethod
    def _apply_achievements(player: dict, achievements: dict) -> None:
        for key, value in achievements.get("achievements", {}).items():
            player.setdefault("achievement", []).append({"type": item("u8", int(key)), "count": item("u32", value)})
        for key, value in achievements.get("charas", {}).items():
            player.setdefault("chara_param", []).append({"chara_id": item("u16", int(key)), "friendship": item("u16", value)})
        for key, value in achievements.get("stories", {}).items():
            player.setdefault("story", []).append({"story_id": item("u32", int(key)), **{name: item("bool" if name == "is_cleared" else "u32", val) for name, val in value.items()}})
        for key, value in achievements.get("items", {}).items():
            try: type_id, item_id = (int(x) for x in key.split(":", 1))
            except ValueError: continue
            player.setdefault("item", []).append({"type": item("u8", type_id), "id": item("u16", item_id), "param": item("u16", value), "is_new": item("bool", False)})
        for key, value in achievements.get("medals", {}).items():
            player.setdefault("medal", []).append({"medal_id": item("s16", int(key)), "level": item("s16", value.get("level", 0)), "exp": item("s32", value.get("exp", 0)), "set_count": item("s32", value.get("set_count", 0)), "get_count": item("s32", value.get("get_count", 0))})
        for key, value in achievements.get("areas", {}).items():
            player.setdefault("area", []).append({"area_id": item("u32", int(key)), "chapter_index": item("u8", value.get("chapter_index", 0)), "gauge_point": item("u16", value.get("gauge_point", 0)), "is_cleared": item("bool", value.get("is_cleared", False)), "diary": item("u32", value.get("diary", 0))})
        for key, value in achievements.get("courses", {}).items():
            player.setdefault("course_data", []).append({"course_id": item("s16", int(key)), "clear_type": item("u8", value.get("clear_type", 0)), "clear_rank": item("u8", value.get("clear_rank", 0)), "total_score": item("s32", value.get("total_score", 0)), "update_count": item("s32", value.get("update_count", 0)), "sheet_num": item("u8", value.get("sheet_num", 0))})
        for key, value in achievements.get("fes", {}).items():
            player.setdefault("fes", []).append({"fes_id": item("u32", int(key)), "chapter_index": item("u8", value.get("chapter_index", 0)), "gauge_point": item("u16", value.get("gauge_point", 0)), "is_cleared": item("bool", value.get("is_cleared", False))})
        for key, value in achievements.get("missions", {}).items():
            player.setdefault("mission", []).append({"mission_id": item("u32", int(key)), "gauge_point": item("u32", value.get("gauge_point", 0)), "mission_comp": item("u32", value.get("mission_comp", 0))})
        for key, value in achievements.get("stamps", {}).items():
            player.setdefault("stamp", []).append({"stamp_id": item("s16", int(key)), "cnt": item("s16", value)})
        if achievements.get("team") or achievements.get("battery"):
            player.setdefault("event_p27", {})["first_play"] = item("bool", not achievements.get("team"))
            player["event_p27"]["elem_first_play"] = item("bool", not achievements.get("battery"))
            player["event_p27"]["team"] = [{"team_id": item("s16", x.get("team_id", 0)), "ex_no": item("s16", x.get("ex_no", 0)), "point": item("u32", x.get("point", 0)), "is_cleared": item("bool", x.get("is_cleared", False))} for x in achievements.get("team", [])]
            player["event_p27"]["battery"] = [{"battery_id": item("s16", x.get("battery_id", 0)), "energy": item("u32", x.get("energy", 0)), "is_cleared": item("bool", x.get("is_cleared", False))} for x in achievements.get("battery", [])]

    async def _scores(self, refid: str) -> dict:
        scores = await self.repo.scores(refid, self.spec.version)
        hiscore = [0] * (((self.spec.max_music * 4) * 17 + 7) // 8)
        medals = [0] * self.spec.max_music
        play_count: dict[int, int] = {}
        for key, value in scores.get("scores", {}).items():
            try: music, sheet = (int(x) for x in key.split(":", 1))
            except ValueError: continue
            if music > self.spec.max_music or sheet not in range(4): continue
            medal = CLEAR_TO_MEDAL.get(value.get("clear_type", 0), 0)
            medals[music] |= medal << (sheet * 4)
            index = music * 4 + sheet
            bit = index * 17
            score = int(value.get("score", 0)) << (bit % 8)
            pos = bit // 8
            if pos < len(hiscore): hiscore[pos] |= score & 0xFF
            if pos + 1 < len(hiscore): hiscore[pos + 1] |= (score >> 8) & 0xFF
            if pos + 2 < len(hiscore): hiscore[pos + 2] |= (score >> 16) & 0xFF
            play_count[music] = play_count.get(music, 0) + int(value.get("cnt", 0))
        return {"hiscore_array": hiscore, "clear_medal": medals, "play_count": play_count}

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
                if isinstance(value, (str, int, float, bool)) or (isinstance(value, list) and all(isinstance(x, (str, int, float, bool)) for x in value)):
                    key = path.rsplit(".", 1)[-1].split("__", 1)[0]
                    values[key] = value[0] if isinstance(value, list) and len(value) == 1 else value
            for key, child_node in node.items():
                if not key.startswith("@"):
                    collect(child_node, f"{path}.{key}" if path else key)

        collect(data)
        await self.repo.save_params(refid, self.spec.version, params)

    async def _save_achievements(self, refid: str, data: dict) -> None:
        defaults = {"collection": "achievements", "version": self.spec.version, "achievements": {}, "stories": {}, "items": {}, "charas": {}, "areas": {}, "courses": {}, "fes": {}, "missions": {}, "riddles": {}, "team": [], "battery": {}}
        achievements = await self.repo.achievements(refid, self.spec.version, defaults)
        for node_name, target, fields in (
            ("achievement", "achievements", ("type", "count")), ("story", "stories", ("story_id", "chapter_id", "gauge_point", "is_cleared", "clear_chapter")),
            ("area", "areas", ("area_id", "chapter_index", "gauge_point", "is_cleared", "diary")), ("course_data", "courses", ("course_id", "clear_type", "clear_rank", "total_score", "update_count", "sheet_num")),
            ("fes", "fes", ("fes_id", "chapter_index", "gauge_point", "is_cleared")), ("mission", "missions", ("mission_id", "gauge_point", "mission_comp")),
        ):
            bucket = achievements.setdefault(target, {})
            for node in elements(data, node_name):
                key = scalar(field(node, fields[0]), 0)
                bucket[str(key)] = {name: scalar(field(node, name), 0) if name != "is_cleared" else bool(scalar(field(node, name), 0)) for name in fields[1:]}
        for node in elements(data, "item"):
            achievements.setdefault("items", {})[f"{scalar(field(node, 'type'))}:{scalar(field(node, 'id'))}"] = scalar(field(node, "param"))
        for node in elements(data, "chara_param"):
            achievements.setdefault("charas", {})[str(scalar(field(node, "chara_id")))] = scalar(field(node, "friendship"))
        for node in elements(data, "medal"):
            achievements.setdefault("medals", {})[str(scalar(field(node, "medal_id")))] = {key: scalar(field(node, key)) for key in ("level", "exp", "set_count", "get_count")}
        for node in elements(data, "stamp"):
            achievements.setdefault("stamps", {})[str(scalar(field(node, "stamp_id")))] = scalar(field(node, "cnt"))
        await self.repo.save_achievements(refid, self.spec.version, achievements)

    @staticmethod
    def _rank(score: Any) -> int:
        score = scalar(score)
        for limit, rank in ((50000, 1), (62000, 2), (72000, 3), (82000, 4), (90000, 5), (95000, 6), (98000, 7)):
            if score < limit:
                return rank
        return 8

    @staticmethod
    def _merge_score(scores: dict, music: int, sheet: int, score: int, clear_type: int) -> None:
        key = f"{music}:{sheet}"
        old = scores.setdefault("scores", {}).get(key)
        if old is None:
            scores["scores"][key] = {"score": score, "cnt": 1, "clear_type": clear_type}
        else:
            old.update(score=max(score, old.get("score", 0)), cnt=old.get("cnt", 0) + 1, clear_type=max(clear_type, old.get("clear_type", 0)))

    @staticmethod
    def _items(values: dict[str, tuple[str, Any]]) -> dict:
        return {key: item(type_name, value) for key, (type_name, value) in values.items()}

    @staticmethod
    def _goods(count: int) -> list[dict]:
        result = []
        for index in range(count):
            price = 150 if index >= 80 else 60
            result.append({"goods_id": item("s16", index), "price": item("s16", price)})
        return result
