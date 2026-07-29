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
        root.append('result', Type.U8, 0) # doesn't seem to matter

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
        cfg.append('sub_category', Type.S8, -1)
        cfg.append('chara_category', Type.S8, -1)
        cfg.append('ms_banner_disp', Type.S8, 0)
        cfg.append('ms_down_info', Type.S8, 0)
        cfg.append('ms_side_info', Type.S8, 0)
        cfg.append('ms_raise_type', Type.S8, 0)
        cfg.append('ms_rnd_type', Type.S8, 0)
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
        try:
            submitted_name = request.xpath("player/name").value
        except Exception:
            submitted_name = None

        if submitted_name:
            name = next((child for child in acct.children if child.name == "name"), None)
            if name is not None:
                name.value = submitted_name

        root.attributes["status"] = "0"
        return root


    async def handle_player_new(self, request: XMLNode) -> XMLNode:
        return await self.handle_player_read(request)

    async def handle_player_conversion(self, request: XMLNode) -> XMLNode:
        return await self.handle_player_read(request)

    async def handle_player_write(self, request: XMLNode) -> XMLNode:
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
