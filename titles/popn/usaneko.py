from core.eamuse import BaseHandler
from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import XMLNode, Type
from datetime import datetime
from typing import List

from .config import PopnConfig
from .const import PopnConstants
from .base import PopnBase


class PopnUsaneko(PopnBase):
    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_USANEKO
        self.extra_services = {"local2": "", "lobby2": ""}
    
    def get_phase_info(self) -> List[XMLNode]:
        out = []
        def add_evt(evt_id: int, phase: int) -> None:
            evt = XMLNode.void('phase')
            evt.append('event_id', Type.S16, evt_id)
            evt.append('phase', Type.S16, phase)
            out.append(evt)
        
        add_evt(0, 255)
        add_evt(1, 4)
        add_evt(2, 0)
        add_evt(3, 1) # net taisen
        add_evt(4, 1)
        add_evt(5, 1) # lab unlock event

        return out

    async def handle_pcb24_boot(self, request: XMLNode) -> XMLNode:
        return XMLNode('pcb24')

    async def handle_info24_common(self, request: XMLNode) -> XMLNode:
        root = XMLNode('info24')

        root.children += self.get_phase_info()

        """
        [2024/09/29 15:56:03] M:automap: property_search error: news
        [2024/09/29 15:56:03] M:automap: property_search error: ranking_info
        [2024/09/29 15:56:03] M:automap: property_search error: area
        [2024/09/29 15:56:03] M:automap: property_search error: choco
        [2024/09/29 15:56:03] M:automap: property_search error: goods
        [2024/09/29 15:56:03] M:automap: property_search error: fes
        [2024/09/29 15:56:03] M:automap: property_search error: popular
        [2024/09/29 15:56:03] M:automap: property_search error: popular_music
        [2024/09/29 15:56:03] M:automap: property_search error: recommend
        [2024/09/29 15:56:03] M:automap: property_search error: mission_point
        [2024/09/29 15:56:03] M:automap: property_search error: medal
        [2024/09/29 15:56:03] M:automap: property_search error: chara_ranking
        [2024/09/29 15:56:03] M:automap: property_search error: musicsub
        [2024/09/29 15:56:03] M:automap: property_search error: tracksub
        [2024/09/29 15:56:03] M:automap: property_search error: charasub
        """

        return root

    async def handle_player24_new(self, request: XMLNode) -> XMLNode:
        root = XMLNode('player24')
        root.append('result', Type.U8, 2)
        return root

    async def handle_player24_start(self, request: XMLNode) -> XMLNode:
        root = await self.handle_info24_common(request)
        root.append('play_id', Type.S32, 1) # doesn't seem to matter, just increment
        return root

    async def handle_player24_read_score(self, request: XMLNode) -> XMLNode:
        root = XMLNode('player24')
        root.append('con_flg', Type.Bool, False) # ?

        for x in []:
            music = XMLNode.void("music")
            music.append('music_num', Type.S16 , 0)
            music.append('sheet_num', Type.U8 , 0)
            music.append('score', Type.S32 , 0)
            music.append('clear_type', Type.U8 , 0)
            music.append('clear_rank', Type.U8 , 0)
            music.append('cnt', Type.S16 , 0)
            root.children.append(music)
        
        return root

    async def handle_player24_read(self, request: XMLNode) -> XMLNode:
        root = XMLNode('player24')
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
        cfg.append('course_id', Type.S16, 0)
        cfg.append('course_folder', Type.S8, 0)
        cfg.append('ms_banner_disp', Type.S8, 0)
        cfg.append('ms_down_info', Type.S8, 0)
        cfg.append('ms_side_info', Type.S8, 0)
        cfg.append('ms_raise_type', Type.S8, 0)
        cfg.append('ms_rnd_type', Type.S8, 0)
        cfg.append('banner_sort', Type.S8, 0)
    
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
        opt.append('lift', Type.Bool, False)
        opt.append('lift_rate', Type.S16, -1)

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
        return root

    async def handle_lobby24_getList(self, request: XMLNode) -> XMLNode:
        root =  XMLNode.void("lobby24")
        
        lst = XMLNode.void('list')
        lst.append(XMLNode('no', Type.U32, 0))
        lst.append(XMLNode('time', Type.U32, 0))
        lst.append(XMLNode('ip', Type.U32, 0))
        lst.append(XMLNode('port', Type.U16, 0))
        lst.append(XMLNode('local_ip', Type.U32, 0))
        lst.append(XMLNode('music', Type.S16, 0))
        lst.append(XMLNode('sheet', Type.U8, 0))
        lst.append(XMLNode('is_ojama', Type.U8, 0))

        return root

    async def handle_lobby24_entry(self, request: XMLNode) -> XMLNode:
        root = XMLNode.void("lobby24")
        
        # TODO: Save/get lobby info
        root.append('no', Type.U32, 1)
        root.append('time', Type.U32, request.xpath("lobby24/time").value)
        root.append('ip', Type.U32, request.xpath("lobby24/ip").value)
        root.append('port', Type.U16, request.xpath("lobby24/port").value)
        root.append('local_ip', Type.U32, request.xpath("lobby24/local_ip").value)
        root.append('music', Type.S16, request.xpath("lobby24/music").value)
        root.append('sheet', Type.U8, request.xpath("lobby24/sheet").value)
        root.append('is_ojama', Type.U8, request.xpath("lobby24/is_ojama").value)

        return root

    async def handle_player24_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24")

    async def handle_player24_write_music(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24")
