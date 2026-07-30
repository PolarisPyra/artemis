from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import XMLNode, Type

from .config import PopnConfig
from .const import PopnConstants
from .jamfizz import PopnJamFizz


class PopnHiCheers(PopnJamFizz):
    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_HI_CHEERS
        self.extra_services.update({"local3": ""})

    @staticmethod
    def _request_value(request: XMLNode, path: str):
        try:
            return request.xpath(path).value
        except Exception:
            return None

    async def _get_profile(self, request: XMLNode):
        ref_id = self._request_value(request, "player/ref_id")
        if not ref_id:
            return None, None

        user_id = await self.data.user.get_user_id_by_refid(ref_id)
        if user_id is None:
            return None, None

        profile = await self.data.profile.get_profile(user_id)
        if profile is None:
            name = self._request_value(request, "player/name") or "なし"
            pref = self._request_value(request, "player/pref") or 0
            profile = await self.data.profile.create_profile(user_id, name, pref)

        return user_id, profile

    @staticmethod
    def _set_child(parent: XMLNode, name: str, value) -> None:
        for child in parent.children:
            if child.name == name:
                child.value = value
                return

    @staticmethod
    def _set_repeated(parent: XMLNode, name: str, values) -> None:
        values = list(values)
        index = 0
        for child in parent.children:
            if child.name == name and index < len(values):
                child.value = values[index]
                index += 1

    @staticmethod
    def _set_array(parent: XMLNode, name: str, values) -> None:
        for child in parent.children:
            if child.name == name:
                child.value = list(values)
                return

    def _apply_profile(self, root: XMLNode, row) -> None:
        if row is None:
            return

        values = row._mapping

        def set_section(section: str, fields) -> None:
            parent = next((child for child in root.children if child.name == section), None)
            if parent is None:
                return
            for xml_name, column in fields.items():
                value = values[column]
                if isinstance(value, list):
                    if xml_name == "dialog":
                        self._set_repeated(parent, xml_name, value)
                    else:
                        self._set_array(parent, xml_name, value)
                else:
                    self._set_child(parent, xml_name, value)

        set_section("account", {
            "name": "name", "g_pm_id": "g_pm_id", "tutorial": "tutorial",
            "area_id": "area_id", "use_navi": "use_navi", "read_news": "read_news",
            "staff": "staff", "item_type": "item_type", "item_id": "item_id",
            "is_conv": "is_conv", "active_fr_num": "active_fr_num",
            "total_play_cnt": "total_play_cnt", "today_play_cnt": "today_play_cnt",
            "consecutive_days": "consecutive_days", "total_days": "total_days",
            "interval_day": "interval_day", "my_best": "my_best",
            "latest_music": "latest_music", "nice": "nice",
            "favorite_chara": "favorite_chara", "special_area": "special_area",
            "chocolate_charalist": "chocolate_charalist",
            "chocolate_sp_chara": "chocolate_sp_chara",
            "chocolate_pass_cnt": "chocolate_pass_cnt", "chocolate_hon_cnt": "chocolate_hon_cnt",
            "teacher_setting": "teacher_setting", "license_data": "license_data",
            "welcom_pack": "welcom_pack", "ranking_node": "ranking_node",
            "chara_ranking_kind_id": "chara_ranking_kind_id",
            "navi_evolution_flg": "navi_evolution_flg",
            "ranking_news_last_no": "ranking_news_last_no", "power_point": "power_point",
            "player_point": "player_point", "power_point_list": "power_point_list",
            "sp_riddles_id": "sp_riddles_id",
        })
        set_section("config", {
            name: name for name in [
                "mode", "chara", "music", "sheet", "category", "sub_category",
                "chara_category", "ms_banner_disp", "ms_down_info", "ms_raise_type",
                "banner_sort", "disp_setting", "h_vol", "hiscore_disp", "lane_type",
                "brightness", "key_beam", "lane_line", "course_id", "course_folder",
            ]
        })
        set_section("option", {
            name: name for name in [
                "hispeed", "popkun", "hidden", "hidden_rate", "sudden", "sudden_rate",
                "randmir", "gauge_type", "ojama_0", "ojama_1", "forever_0", "forever_1",
                "full_setting", "judge", "guide_se", "guide_se_vol", "lift", "lift_rate",
                "judge_ad", "roof", "long_pop",
            ]
        })
        set_section("custom_cate", {
            xml_name: f"custom_{xml_name}"
            for xml_name in ["valid", "lv_min", "lv_max", "medal_min", "medal_max", "friend_no", "score_flg"]
        })
        set_section("customize", {
            name: name for name in ["effect_left", "effect_center", "effect_right", "hukidashi", "comment_1", "comment_2"]
        })
        set_section("eaappli", {"relation": "relation"})
        set_section("info", {"ep": "ep"})
        set_section("netvs", {
            "record": "netvs_record", "ojama_condition": "ojama_condition",
            "set_ojama": "set_ojama", "set_recommend": "set_recommend",
            "netvs_play_cnt": "netvs_play_cnt",
        })
        stamp = next((child for child in root.children if child.name == "stamp"), None)
        if stamp is not None:
            self._set_child(stamp, "stamp_id", values["stamp_id"])
            self._set_child(stamp, "cnt", values["stamp_cnt"])
        event = next((child for child in root.children if child.name == "event2021"), None)
        if event is not None:
            set_values = {
                "point": "event2021_point", "step": "event2021_step",
                "quest_point": "event2021_quest_point", "step_nos": "event2021_step_nos",
                "quest_point_nos": "event2021_quest_point_nos",
            }
            for xml_name, column in set_values.items():
                value = values[column]
                self._set_array(event, xml_name, value) if isinstance(value, list) else self._set_child(event, xml_name, value)
        event = next((child for child in root.children if child.name == "event_p27"), None)
        if event is not None:
            for xml_name, column in {
                "team_id": "event_p27_team_id", "first_play": "event_p27_first_play",
                "select_battery_id": "event_p27_select_battery_id", "elem_first_play": "event_p27_elem_first_play",
                "today_first_play": "event_p27_today_first_play",
            }.items():
                self._set_child(event, xml_name, values[column])
            teams = values["event_p27_teams"]
            for child, team in zip([child for child in event.children if child.name == "team"], teams):
                for field in ["team_id", "ex_no", "point", "is_cleared"]:
                    self._set_child(child, field, team[field])

    async def handle_pcb_boot(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_error(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_info_common(self, request: XMLNode) -> XMLNode:
        root = await self.handle_info24_common(request)
        root.name = "info"
        return root

    async def handle_player_read(self, request: XMLNode) -> XMLNode:
        _, profile = await self._get_profile(request)
        root = XMLNode('player')
        """
        [2024/09/28 04:03:14] M:automap: property_search error: course_data ( course_id S16, clear_type U8, clear_rank U8, total_score S32, update_count S32, sheet_num U8 )
        [2024/09/28 04:03:14] M:automap: property_search error: navi_data (
            raisePoint -> raisePoint S32[54],
            navi_param -> navi_id U16, friendship S32
        )
        [2024/09/28 04:03:14] M:automap: property_search error: area ( area_id U32, chapter_index U8, gauge_point U16, is_cleared Bool, diary U32 )
        [2024/09/28 04:03:14] M:automap: property_search error: fes ( fes_id U32, chapter_index U8, gauge_point U16, is_cleared Bool )
        [2024/09/28 04:03:14] M:automap: property_search error: mission ( mission_id U32, gauge_point U32, mission_comp U32 )
        [2024/09/28 04:03:14] M:automap: property_search error: riddles_data (
            sp_riddles -> kaimei_gauge U16, is_cleared Bool, riddles_cleared Bool, select_count U8, other_count U32
            sh_riddles ->  sh_riddles_id U32
        )
        """
        acct = XMLNode.void("account")
        acct.append('g_pm_id', Type.Str, '123456789012')
        acct.append('name', Type.Str, 'ＨＡＹ１ＴＳ')
        acct.append('tutorial', Type.S16, 308)
        acct.append('area_id', Type.S16, 0)
        acct.append('use_navi', Type.S16, 0)
        acct.append('read_news', Type.S16, 0)
        acct.append('staff', Type.S8, 0)
        acct.append('item_type', Type.S16, 0)
        acct.append('item_id', Type.S16, 0)
        acct.append('is_conv', Type.S8, 0)
        acct.append('active_fr_num', Type.U8, 0)
        acct.append('total_play_cnt', Type.S16, 2) # 0 or 1 triggers first play free, 0 acts as not first play for tutorials?
        acct.append('today_play_cnt', Type.S16, 1)
        acct.append('consecutive_days', Type.S16, 1)
        acct.append('total_days', Type.S16, 1)
        acct.append('interval_day', Type.S16, 0)
        acct.append('my_best', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('latest_music', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('nice', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('favorite_chara', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('special_area', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('chocolate_charalist', Type.S16, [-1, -1, -1, -1, -1])
        acct.append('chocolate_sp_chara', Type.S32, 0)
        acct.append('chocolate_pass_cnt', Type.S32, 0)
        acct.append('chocolate_hon_cnt', Type.S32, 0)
        acct.append('teacher_setting', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('license_data', Type.S16, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('welcom_pack', Type.Bool, False) # Always grants extra stage
        acct.append('ranking_node', Type.S32, 0)
        acct.append('chara_ranking_kind_id', Type.S32, 0)
        acct.append('navi_evolution_flg', Type.S8, 0)
        acct.append('ranking_news_last_no', Type.S32, 0)
        acct.append('power_point', Type.S32, 0)
        acct.append('player_point', Type.S32, 300)
        acct.append('power_point_list', Type.S32, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        acct.append('sp_riddles_id', Type.S16, 0)

        info = XMLNode.void('info')
        info.append('ep', Type.U16, 0)

        eaappli = XMLNode.void("eaappli")
        eaappli.append('relation', Type.S8, 1)

        cfg = XMLNode.void("config")
        cfg.append('mode', Type.U8, 0)
        cfg.append('chara', Type.S16, -1)
        cfg.append('music', Type.S16, -1)
        cfg.append('sheet', Type.U8, 0)
        cfg.append('category', Type.S8, -1)
        cfg.append('sub_category', Type.S16, -1)
        cfg.append('chara_category', Type.S16, -1)
        cfg.append('ms_banner_disp', Type.U8, 0)
        cfg.append('ms_down_info', Type.S8, 0)
        cfg.append('ms_raise_type', Type.S8, 0)
        cfg.append('banner_sort', Type.S8, 0)
        cfg.append('disp_setting', Type.S8, 0)
        cfg.append('h_vol', Type.S8, 0)
        cfg.append('hiscore_disp', Type.S8, 0)
        cfg.append('lane_type', Type.S8, 0)
        cfg.append('brightness', Type.S8, 0)
        cfg.append('key_beam', Type.S8, 0)
        cfg.append('lane_line', Type.S8, 0)
        cfg.append('course_id', Type.S16, 0)
        cfg.append('course_folder', Type.S8, 0)

        opt = XMLNode.void("option")
        opt.append('hispeed', Type.S16, 10)
        opt.append('popkun', Type.U8, 0)
        opt.append('hidden', Type.Bool, False)
        opt.append('hidden_rate', Type.S16, -1)
        opt.append('sudden', Type.Bool, False)
        opt.append('sudden_rate', Type.S16, -1)
        opt.append('randmir', Type.S8, 0)
        opt.append('gauge_type', Type.S8, 0)
        opt.append('ojama_0', Type.U8, 0)
        opt.append('ojama_1', Type.U8, 0)
        opt.append('forever_0', Type.Bool, False)
        opt.append('forever_1', Type.Bool, False)
        opt.append('full_setting', Type.Bool, True)
        opt.append('judge', Type.U8, 1)
        opt.append('guide_se', Type.S8, 0)
        opt.append('guide_se_vol', Type.U8, 0)
        opt.append('lift', Type.Bool, False)
        opt.append('lift_rate', Type.S16, -1)
        opt.append('judge_ad', Type.S8, 0)
        opt.append('roof', Type.S16, 0)
        opt.append('long_pop', Type.Bool, False)

        cate = XMLNode.void("custom_cate")
        cate.append('valid', Type.S8, 0)
        cate.append('lv_min', Type.S8, -1)
        cate.append('lv_max', Type.S8, -1)
        cate.append('medal_min', Type.S8, -1)
        cate.append('medal_max', Type.S8, -1)
        cate.append('friend_no', Type.S8, -1)
        cate.append('score_flg', Type.S8, -1)

        custom = XMLNode.void('customize')
        custom.append('effect_left', Type.U16, 0)
        custom.append('effect_center', Type.U16, 0)
        custom.append('effect_right', Type.U16, 0)
        custom.append('hukidashi', Type.U16, 0)
        custom.append('comment_1', Type.U16, 0)
        custom.append('comment_2', Type.U16, 0)

        netvs = XMLNode.void('netvs')
        netvs.append('record', Type.S16, [0, 0, 0, 0, 0, 0])
        netvs.append('dialog', Type.Str, '')
        netvs.append('dialog', Type.Str, '')
        netvs.append('dialog', Type.Str, '')
        netvs.append('dialog', Type.Str, '')
        netvs.append('dialog', Type.Str, '')
        netvs.append('dialog', Type.Str, '')
        netvs.append('ojama_condition', Type.S8, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        netvs.append('set_ojama', Type.S8, [0, 0, 0])
        netvs.append('set_recommend', Type.S8, [0, 0, 0])
        netvs.append('netvs_play_cnt', Type.U32, 0)

        for x in []:
            friend = XMLNode.void("friend")
            friend.append("no", Type.S16, x)
            friend.append("g_pm_id", Type.Str, "")
            friend.append("name", Type.Str, "")
            friend.append("chara_num", Type.S16, 1)
            friend.append("is_open", Type.S8, 1)

            for y in []:
                friend.append(XMLNode.void("music", {"music_num": "", "sheet_num": "", "score": "", "clearrank": "", "cleartype": ""}))

            for y in []:
                fcourse = XMLNode.void("course_data")
                fcourse.append('course_id', Type.S16, 1)
                fcourse.append('clear_type', Type.U8, 0)
                fcourse.append('clear_rank', Type.U8, 0)
                fcourse.append('total_score', Type.S32, 0)
                fcourse.append('update_count', Type.S32, 0)
                fcourse.append('sheet_num', Type.U8, 0)
                friend.children.append(fcourse)

            root.children.append(friend)

        for x in []:
            charprm = XMLNode.void('chara_param')
            charprm.append('chara_id', Type.U16, 0)
            charprm.append('friendship', Type.U16, 0)
            root.children.append(charprm)

        for x in []:
            itm = XMLNode.void('item')
            itm.append('type', Type.U8, 0)
            itm.append('id', Type.U16, 0)
            itm.append('param', Type.U16, 0)
            itm.append('is_new', Type.Bool, False)
            itm.append('get_time', Type.U64, 0)
            root.children.append(itm)

        stamp = XMLNode.void("stamp")
        stamp.append("stamp_id", Type.S16, 0)
        stamp.append("cnt", Type.S16, 0)

        evt2021 = XMLNode.void("event2021")
        evt2021.append("point", Type.U32, 0)
        evt2021.append("step", Type.U8, 0)
        evt2021.append("quest_point", Type.U32, [0] * 8)
        evt2021.append("step_nos", Type.U8, 0)
        evt2021.append("quest_point_nos", Type.U32, [0] * 13)

        evt27 = XMLNode.void("event_p27")
        evt27.append("team_id", Type.S16, 0)
        evt27.append("first_play", Type.Bool, True) # show tutorial
        evt27.append("select_battery_id", Type.S16, 0)
        evt27.append("elem_first_play", Type.Bool, True)
        evt27.append("today_first_play", Type.Bool, True)

        for x in range(8):
            evt27_team = XMLNode.void("team")
            evt27_team.append("team_id", Type.S16, x)
            evt27_team.append("ex_no", Type.S16, 0)
            evt27_team.append("point", Type.U32, 0)
            evt27_team.append("is_cleared", Type.Bool, False)
            evt27.children.append(evt27_team)

        root.children.append(acct)
        root.children.append(cfg)
        root.children.append(opt)
        root.children.append(cate)
        root.children.append(custom)
        root.children.append(eaappli)
        root.children.append(info)
        root.children.append(netvs)
        root.children.append(stamp)
        root.children.append(evt2021)
        root.children.append(evt27)
        self._apply_profile(root, profile)

        root.attributes["status"] = "0"
        return root


    async def handle_player_new(self, request: XMLNode) -> XMLNode:
        root = await self.handle_player_read(request)
        root.append('result', Type.U8, 0)
        return root

    async def handle_player_conversion(self, request: XMLNode) -> XMLNode:
        root = await self.handle_player_read(request)
        root.append('result', Type.U8, 0)
        return root

    async def handle_player_write(self, request: XMLNode) -> XMLNode:
        user_id, _ = await self._get_profile(request)
        if user_id is not None:
            values = {}
            for section, names in {
                "player/account": ["name", "tutorial", "read_news", "sp_riddles_id"],
                "player/config": [
                    "mode", "chara", "music", "sheet", "category", "sub_category",
                    "chara_category", "ms_banner_disp", "ms_down_info", "ms_raise_type",
                    "banner_sort", "disp_setting", "h_vol", "hiscore_disp", "lane_type",
                    "brightness", "key_beam", "lane_line", "course_id", "course_folder",
                ],
                "player/option": [
                    "hispeed", "popkun", "hidden", "hidden_rate", "sudden", "sudden_rate",
                    "randmir", "gauge_type", "ojama_0", "ojama_1", "forever_0", "forever_1",
                    "full_setting", "judge", "guide_se", "guide_se_vol", "lift", "lift_rate",
                    "judge_ad", "roof", "long_pop",
                ],
            }.items():
                for name in names:
                    value = self._request_value(request, f"{section}/{name}")
                    if value is not None:
                        values[name] = value
            await self.data.profile.update_profile(user_id, values)
        return XMLNode.void("player")

    async def handle_player_start(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_end(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_logout(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_write_music(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_friend(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_write_course(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_update_ranking(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_buy(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_read_score(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_tsumtsum(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_read_option(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_loctest24_log(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("loctest24")

    async def handle_lobby24_update(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("lobby24")

    async def handle_lobby24_delete(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("lobby24")

    async def handle_sppass_open(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")

    async def handle_sppass_lookup(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")

    async def handle_sppass_close(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("sppass")
