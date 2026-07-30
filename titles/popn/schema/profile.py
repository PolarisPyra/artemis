from typing import Any, Dict

from sqlalchemy import Column, Table, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Boolean, Integer, JSON, String

from core.data.schema import BaseData, metadata


profile = Table(
    "popn_profile",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False, autoincrement=True),
    Column(
        "user",
        Integer,
        ForeignKey(
            "aime_user.id",
            name="popn_profile_user_fk",
            ondelete="cascade",
            onupdate="cascade",
        ),
        nullable=False,
        unique=True,
    ),
    Column("name", String(32), nullable=False),
    Column("pref", Integer, nullable=False),
    Column("g_pm_id", String(32), nullable=False),
    Column("tutorial", Integer, nullable=False),
    Column("area_id", Integer, nullable=False),
    Column("use_navi", Integer, nullable=False),
    Column("read_news", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("item_type", Integer, nullable=False),
    Column("item_id", Integer, nullable=False),
    Column("is_conv", Integer, nullable=False),
    Column("active_fr_num", Integer, nullable=False),
    Column("total_play_cnt", Integer, nullable=False),
    Column("today_play_cnt", Integer, nullable=False),
    Column("consecutive_days", Integer, nullable=False),
    Column("total_days", Integer, nullable=False),
    Column("interval_day", Integer, nullable=False),
    Column("my_best", JSON, nullable=False),
    Column("latest_music", JSON, nullable=False),
    Column("nice", JSON, nullable=False),
    Column("favorite_chara", JSON, nullable=False),
    Column("special_area", JSON, nullable=False),
    Column("chocolate_charalist", JSON, nullable=False),
    Column("chocolate_sp_chara", Integer, nullable=False),
    Column("chocolate_pass_cnt", Integer, nullable=False),
    Column("chocolate_hon_cnt", Integer, nullable=False),
    Column("teacher_setting", JSON, nullable=False),
    Column("license_data", JSON, nullable=False),
    Column("welcom_pack", Boolean, nullable=False),
    Column("ranking_node", Integer, nullable=False),
    Column("chara_ranking_kind_id", Integer, nullable=False),
    Column("navi_evolution_flg", Integer, nullable=False),
    Column("ranking_news_last_no", Integer, nullable=False),
    Column("power_point", Integer, nullable=False),
    Column("player_point", Integer, nullable=False),
    Column("power_point_list", JSON, nullable=False),
    Column("sp_riddles_id", Integer, nullable=False),
    Column("mode", Integer, nullable=False),
    Column("chara", Integer, nullable=False),
    Column("music", Integer, nullable=False),
    Column("sheet", Integer, nullable=False),
    Column("category", Integer, nullable=False),
    Column("sub_category", Integer, nullable=False),
    Column("chara_category", Integer, nullable=False),
    Column("ms_banner_disp", Integer, nullable=False),
    Column("ms_down_info", Integer, nullable=False),
    Column("ms_raise_type", Integer, nullable=False),
    Column("banner_sort", Integer, nullable=False),
    Column("disp_setting", Integer, nullable=False),
    Column("h_vol", Integer, nullable=False),
    Column("hiscore_disp", Integer, nullable=False),
    Column("lane_type", Integer, nullable=False),
    Column("brightness", Integer, nullable=False),
    Column("key_beam", Integer, nullable=False),
    Column("lane_line", Integer, nullable=False),
    Column("course_id", Integer, nullable=False),
    Column("course_folder", Integer, nullable=False),
    Column("hispeed", Integer, nullable=False),
    Column("popkun", Integer, nullable=False),
    Column("hidden", Boolean, nullable=False),
    Column("hidden_rate", Integer, nullable=False),
    Column("sudden", Boolean, nullable=False),
    Column("sudden_rate", Integer, nullable=False),
    Column("randmir", Integer, nullable=False),
    Column("gauge_type", Integer, nullable=False),
    Column("ojama_0", Integer, nullable=False),
    Column("ojama_1", Integer, nullable=False),
    Column("forever_0", Boolean, nullable=False),
    Column("forever_1", Boolean, nullable=False),
    Column("full_setting", Boolean, nullable=False),
    Column("judge", Integer, nullable=False),
    Column("guide_se", Integer, nullable=False),
    Column("guide_se_vol", Integer, nullable=False),
    Column("lift", Boolean, nullable=False),
    Column("lift_rate", Integer, nullable=False),
    Column("judge_ad", Integer, nullable=False),
    Column("roof", Integer, nullable=False),
    Column("long_pop", Boolean, nullable=False),
    Column("custom_valid", Integer, nullable=False),
    Column("custom_lv_min", Integer, nullable=False),
    Column("custom_lv_max", Integer, nullable=False),
    Column("custom_medal_min", Integer, nullable=False),
    Column("custom_medal_max", Integer, nullable=False),
    Column("custom_friend_no", Integer, nullable=False),
    Column("custom_score_flg", Integer, nullable=False),
    Column("effect_left", Integer, nullable=False),
    Column("effect_center", Integer, nullable=False),
    Column("effect_right", Integer, nullable=False),
    Column("hukidashi", Integer, nullable=False),
    Column("comment_1", Integer, nullable=False),
    Column("comment_2", Integer, nullable=False),
    Column("relation", Integer, nullable=False),
    Column("ep", Integer, nullable=False),
    Column("netvs_record", JSON, nullable=False),
    Column("netvs_dialog", JSON, nullable=False),
    Column("ojama_condition", JSON, nullable=False),
    Column("set_ojama", JSON, nullable=False),
    Column("set_recommend", JSON, nullable=False),
    Column("netvs_play_cnt", Integer, nullable=False),
    Column("stamp_id", Integer, nullable=False),
    Column("stamp_cnt", Integer, nullable=False),
    Column("event2021_point", Integer, nullable=False),
    Column("event2021_step", Integer, nullable=False),
    Column("event2021_quest_point", JSON, nullable=False),
    Column("event2021_step_nos", Integer, nullable=False),
    Column("event2021_quest_point_nos", JSON, nullable=False),
    Column("event_p27_team_id", Integer, nullable=False),
    Column("event_p27_first_play", Boolean, nullable=False),
    Column("event_p27_select_battery_id", Integer, nullable=False),
    Column("event_p27_elem_first_play", Boolean, nullable=False),
    Column("event_p27_today_first_play", Boolean, nullable=False),
    Column("event_p27_teams", JSON, nullable=False),
    # Hi~Cheers adds these fields to the account/config payload.
    Column("popn_class", Integer, nullable=False),
    Column("option_tuto", Boolean, nullable=False),
    Column("sc_news_no", Integer, nullable=False),
    Column("read_policy", Integer, nullable=False),
    Column("language", Integer, nullable=False),
    Column("customize", JSON, nullable=False),
    mysql_charset="utf8mb4",
)


def _defaults(name: str, pref: int) -> Dict[str, Any]:
    return {
        "name": name,
        "pref": pref,
        "g_pm_id": "123456789012",
        "tutorial": 308,
        "area_id": 0,
        "use_navi": 0,
        "read_news": 0,
        "staff": 0,
        "item_type": 0,
        "item_id": 0,
        "is_conv": 0,
        "active_fr_num": 0,
        "total_play_cnt": 0,
        "today_play_cnt": 0,
        "consecutive_days": 0,
        "total_days": 0,
        "interval_day": 0,
        "my_best": [-1] * 20,
        "latest_music": [-1] * 30,
        "nice": [-1] * 100,
        "favorite_chara": [-1] * 100,
        "special_area": [-1] * 8,
        "chocolate_charalist": [-1] * 5,
        "chocolate_sp_chara": 0,
        "chocolate_pass_cnt": 0,
        "chocolate_hon_cnt": 0,
        "teacher_setting": [-1] * 10,
        "license_data": [-1] * 20,
        "welcom_pack": False,
        "ranking_node": 0,
        "chara_ranking_kind_id": 0,
        "navi_evolution_flg": 0,
        "ranking_news_last_no": 0,
        "power_point": 0,
        "player_point": 300,
        "power_point_list": [-1] * 20,
        "sp_riddles_id": 0,
        "mode": 0, "chara": -1, "music": -1, "sheet": 0,
        "category": -1, "sub_category": -1, "chara_category": -1,
        "ms_banner_disp": 0, "ms_down_info": 0, "ms_raise_type": 0,
        "banner_sort": 0, "disp_setting": 0, "h_vol": 0,
        "hiscore_disp": 0, "lane_type": 0, "brightness": 50,
        "key_beam": 0, "lane_line": 0, "course_id": 0, "course_folder": 0,
        "hispeed": 10, "popkun": 0, "hidden": False, "hidden_rate": -1,
        "sudden": False, "sudden_rate": -1, "randmir": 0, "gauge_type": 0,
        "ojama_0": 0, "ojama_1": 0, "forever_0": False, "forever_1": False,
        "full_setting": True, "judge": 1, "guide_se": 0, "guide_se_vol": 0,
        "lift": False, "lift_rate": -1, "judge_ad": 0, "roof": 0,
        "long_pop": False,
        "custom_valid": 0, "custom_lv_min": -1, "custom_lv_max": -1,
        "custom_medal_min": -1, "custom_medal_max": -1, "custom_friend_no": -1,
        "custom_score_flg": -1,
        "effect_left": 0, "effect_center": 0, "effect_right": 0,
        "hukidashi": 0, "comment_1": 0, "comment_2": 0,
        "relation": 1, "ep": 0,
        "netvs_record": [0] * 6, "netvs_dialog": [""] * 6,
        "ojama_condition": [0] * 74, "set_ojama": [0] * 3,
        "set_recommend": [0] * 3, "netvs_play_cnt": 0,
        "stamp_id": 0, "stamp_cnt": 0,
        "event2021_point": 0, "event2021_step": 0,
        "event2021_quest_point": [0] * 8, "event2021_step_nos": 0,
        "event2021_quest_point_nos": [0] * 13,
        "event_p27_team_id": 0, "event_p27_first_play": True,
        "event_p27_select_battery_id": 0, "event_p27_elem_first_play": True,
        "event_p27_today_first_play": True, "event_p27_teams": [
            {"team_id": team_id, "ex_no": 0, "point": 0, "is_cleared": False}
            for team_id in range(8)
        ],
        "popn_class": 0,
        "option_tuto": False,
        "sc_news_no": 0,
        "read_policy": 0,
        "language": 0,
        "customize": {
            "seal_0": 0, "seal_1": 0, "seal_2": 0, "seal_3": 0,
            "seal_4": 0, "seal_5": 0, "seal_6": 0, "seat": 0,
            "touch_th": 0, "lane_cover": 0, "stage_bk": 0, "highlight": 0,
        },
    }


class PopnProfileData(BaseData):
    async def get_profile(self, user_id: int):
        result = await self.execute(select(profile).where(profile.c.user == user_id))
        return None if result is None else result.fetchone()

    async def get_profile_data(self, user_id: int) -> Dict[str, Any] | None:
        row = await self.get_profile(user_id)
        return None if row is None else dict(row._mapping)

    async def create_profile(self, user_id: int, name: str, pref: int):
        values = _defaults(name, pref)
        values["user"] = user_id
        values["g_pm_id"] = f"{user_id:012d}"
        statement = insert(profile).values(**values)
        conflict = statement.on_duplicate_key_update(
            name=statement.inserted.name,
            pref=statement.inserted.pref,
        )
        result = await self.execute(conflict)
        if result is None:
            self.logger.error("Failed to create Pop'n profile for user %s", user_id)
            return None
        return await self.get_profile(user_id)

    async def create_profile_data(
        self, user_id: int, name: str, pref: int
    ) -> Dict[str, Any] | None:
        row = await self.create_profile(user_id, name, pref)
        return None if row is None else dict(row._mapping)

    async def update_profile(self, user_id: int, values: Dict[str, Any]) -> bool:
        values = {key: value for key, value in values.items() if key in profile.c}
        if not values:
            return True
        result = await self.execute(profile.update(profile.c.user == user_id).values(**values))
        return result is not None
