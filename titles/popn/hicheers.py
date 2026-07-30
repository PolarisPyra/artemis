from typing import Any, Dict, List, Optional

from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import Type, XMLNode

from .config import PopnConfig
from .const import PopnConstants
from .jamfizz import PopnJamFizz


class PopnHiCheers(PopnJamFizz):
    """The M39 Hi~Cheers player protocol.

    Hi~Cheers uses the same card-management services as the earlier Pop'n
    versions, but its player payload is different.  The handlers below keep
    the complete request/response shape from the captured M39 sessions and
    persist the state that is sent by the game.
    """

    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_HI_CHEERS
        self.extra_services.update(
            {"local": "", "lobby": "", "local2": "", "local3": "", "lobby2": ""}
        )

    @staticmethod
    def _value(request: XMLNode, path: str, default: Any = None) -> Any:
        try:
            value = request.xpath(path).value
            # Container nodes created with XMLNode.void use an empty tuple as
            # their value. Treat that as absent when reading scalar fields.
            return default if value == () else value
        except Exception:
            return default

    @staticmethod
    def _player(request: XMLNode) -> Optional[XMLNode]:
        return next(
            (child for child in request.children if child.name == "player"), None
        )

    @staticmethod
    def _row_value(row, key: str, default: Any = None) -> Any:
        if row is None:
            return default
        if isinstance(row, dict):
            value = row.get(key, default)
            return default if value is None else value
        try:
            value = row._mapping[key]
        except (KeyError, TypeError):
            return default
        return default if value is None else value

    async def _get_profile(self, request: XMLNode):
        ref_id = self._value(request, "player/ref_id")
        if not ref_id:
            return None, None

        user_id = await self.data.user.get_user_id_by_refid(ref_id)
        if user_id is None:
            return None, None

        profile = await self.data.profile.get_profile_data(user_id)
        if profile is None:
            name = self._value(request, "player/name", "なし") or "なし"
            pref = self._value(request, "player/pref", 0)
            profile = await self.data.profile.create_profile_data(
                user_id, name, pref or 0
            )

        return user_id, profile

    def _append_account(self, root: XMLNode, row, fresh: bool = False) -> None:
        account = XMLNode.void("account")
        account.append("g_pm_id", Type.Str, self._row_value(row, "g_pm_id", "000000000000"))
        account.append("name", Type.Str, self._row_value(row, "name", "なし"))
        account.append("read_news", Type.S16, 0 if fresh else self._row_value(row, "read_news", 0))
        account.append("nice", Type.S16, self._row_value(row, "nice", [-1] * 100))
        account.append("favorite_chara", Type.S16, self._row_value(row, "favorite_chara", [-1] * 100))
        account.append("power_point", Type.S32, self._row_value(row, "power_point", 0))
        account.append("player_point", Type.S32, self._row_value(row, "player_point", 300))
        account.append("power_point_list", Type.S32, self._row_value(row, "power_point_list", [-1] * 20))
        account.append("tutorial", Type.S16, 0 if fresh else self._row_value(row, "tutorial", 0))
        account.append("is_conv", Type.S8, self._row_value(row, "is_conv", 0))
        account.append("latest_music", Type.S16, self._row_value(row, "latest_music", [-1] * 30))
        account.append("total_play_cnt", Type.S16, 1 if fresh else self._row_value(row, "total_play_cnt", 0))
        account.append("active_fr_num", Type.U8, self._row_value(row, "active_fr_num", 0))
        account.append("popn_class", Type.S8, self._row_value(row, "popn_class", 0))
        account.append("option_tuto", Type.Bool, self._row_value(row, "option_tuto", False))
        account.append("sc_news_no", Type.S32, self._row_value(row, "sc_news_no", 0))
        account.append("read_policy", Type.S16, self._row_value(row, "read_policy", 0))
        account.append("language", Type.S8, self._row_value(row, "language", 0))
        root.children.append(account)

    def _append_profile_sections(self, root: XMLNode, row, fresh: bool = False) -> None:
        self._append_account(root, row, fresh)

        eaappli = XMLNode.void("eaappli")
        eaappli.append("relation", Type.S8, -1 if fresh else self._row_value(row, "relation", 1))
        root.children.append(eaappli)

        info = XMLNode.void("info")
        info.append("ep", Type.U16, self._row_value(row, "ep", 0))
        info.append("estatus", Type.U16, 0)
        root.children.append(info)

        config = XMLNode.void("config")
        config.append("mode", Type.U8, self._row_value(row, "mode", 0))
        config.append("chara", Type.S16, self._row_value(row, "chara", -1))
        config.append("music", Type.S16, self._row_value(row, "music", -1))
        config.append("sheet", Type.U8, self._row_value(row, "sheet", 0))
        config.append("category", Type.S8, self._row_value(row, "category", -1))
        config.append("sub_category", Type.S8, self._row_value(row, "sub_category", -1))
        config.append("chara_category", Type.S8, self._row_value(row, "chara_category", -1))
        config.append("ms_banner_disp", Type.S8, -1 if fresh else self._row_value(row, "ms_banner_disp", 0))
        config.append("ms_down_info", Type.S8, -1 if fresh else self._row_value(row, "ms_down_info", 0))
        config.append("ms_raise_type", Type.S8, -1 if fresh else self._row_value(row, "ms_raise_type", 0))
        config.append("banner_sort", Type.S8, -1 if fresh else self._row_value(row, "banner_sort", 0))
        config.append("disp_setting", Type.S8, -1 if fresh else self._row_value(row, "disp_setting", 0))
        config.append("h_vol", Type.S8, -1 if fresh else self._row_value(row, "h_vol", 0))
        config.append("hiscore_disp", Type.Bool, self._row_value(row, "hiscore_disp", False))
        config.append("lane_type", Type.S8, -1 if fresh else self._row_value(row, "lane_type", 0))
        config.append("brightness", Type.S8, self._row_value(row, "brightness", 50))
        config.append("key_beam", Type.S8, -1 if fresh else self._row_value(row, "key_beam", 0))
        config.append("lane_line", Type.S8, -1 if fresh else self._row_value(row, "lane_line", 0))
        root.children.append(config)

        option = XMLNode.void("option")
        option.append("hispeed", Type.S16, 0 if fresh else self._row_value(row, "hispeed", 10))
        option.append("popkun", Type.U8, self._row_value(row, "popkun", 0))
        option.append("hidden", Type.Bool, self._row_value(row, "hidden", False))
        option.append("hidden_rate", Type.S16, 0 if fresh else self._row_value(row, "hidden_rate", -1))
        option.append("sudden", Type.Bool, self._row_value(row, "sudden", False))
        option.append("sudden_rate", Type.S16, 0 if fresh else self._row_value(row, "sudden_rate", -1))
        option.append("randmir", Type.S8, self._row_value(row, "randmir", 0))
        option.append("gauge_type", Type.S8, self._row_value(row, "gauge_type", 0))
        option.append("ojama_0", Type.U8, self._row_value(row, "ojama_0", 0))
        option.append("ojama_1", Type.U8, self._row_value(row, "ojama_1", 0))
        option.append("forever_0", Type.Bool, self._row_value(row, "forever_0", False))
        option.append("forever_1", Type.Bool, self._row_value(row, "forever_1", False))
        option.append("full_setting", Type.Bool, False if fresh else self._row_value(row, "full_setting", True))
        option.append("judge", Type.U8, 0 if fresh else self._row_value(row, "judge", 1))
        option.append("guide_se", Type.S8, self._row_value(row, "guide_se", 0))
        option.append("lift", Type.Bool, self._row_value(row, "lift", False))
        option.append("lift_rate", Type.S16, 0 if fresh else self._row_value(row, "lift_rate", -1))
        option.append("judge_ad", Type.S8, self._row_value(row, "judge_ad", 0))
        option.append("roof", Type.S16, self._row_value(row, "roof", 0))
        option.append("long_pop", Type.S8, self._row_value(row, "long_pop", 0))
        root.children.append(option)

        custom_cate = XMLNode.void("custom_cate")
        custom_cate.append("valid", Type.S8, 0)
        custom_cate.append("lv_min", Type.S8, -1)
        custom_cate.append("lv_max", Type.S8, -1)
        custom_cate.append("medal_min", Type.S8, -1)
        custom_cate.append("medal_max", Type.S8, -1)
        custom_cate.append("friend_no", Type.S8, -1)
        custom_cate.append("score_flg", Type.S8, -1)
        root.children.append(custom_cate)

        root.children.append(XMLNode.void("navi_data"))

        item_mask = bytes.fromhex(
            "3df7b7ff4fb9bfe2f7d77af7b7dfdaffffdfffffff7bff3f9fffffffff00000000bcfff8ff1cf8ff0f00e0ff3fb7ffff3f006cbfffaf1fc0fbddfdf8f09fffafeff7f70bffffefffffff27fefffffffffff9fdfffdffffcfffffdffffffff5a7f8fffffffffffcff9fffffffffffffff29f97fffffffffffff02e1fff0ffffffffffffff2ffffffffffffdffff3f80fffffffffffffff7ffcfffffbfffdfffff0000f0ff8fffffdffeffffffffffffffff7ffcffbffffffbd3fffffeffffff0b80feffdbf3fffffffffdffdffffff7fffffffdfffffffffefffffffffffffffdfffffffffbfffffff9fffffffffffefdfffbffffffffffc7fff7ffff27fafffbfff8ffffffffffffffffffffffff27f9ffffffffffffffffffffffffffffbffbfcffffffffffffe73f"
        )

        for item_id in range(len(item_mask) * 8):
            if not item_mask[item_id // 8] & (1 << (item_id % 8)):
                continue
            item = XMLNode.void("item")
            item.append("type", Type.U8, 0)
            item.append("id", Type.U16, item_id)
            item.append("param", Type.U16, 15)
            item.append("is_new", Type.Bool, False)
            item.append("get_time", Type.U64, 0)
            root.children.append(item)

        for mission_id in (140, 213, 95) if fresh else (142, 197, 3):
            mission = XMLNode.void("mission")
            mission.append("mission_id", Type.U32, mission_id)
            mission.append("gauge_point", Type.U32, 0)
            mission.append("mission_comp", Type.U32, 0)
            root.children.append(mission)

        netvs = XMLNode.void("netvs")
        netvs.append("record", Type.S16, self._row_value(row, "netvs_record", [0] * 6))
        netvs.append("dialog", Type.Str, "")
        netvs.append("dialog", Type.Str, "")
        netvs.append("dialog", Type.Str, "")
        netvs.append("dialog", Type.Str, "")
        netvs.append("dialog", Type.Str, "")
        netvs.append("dialog", Type.Str, "")
        netvs.append("ojama_condition", Type.S8, self._row_value(row, "ojama_condition", [0] * 74))
        netvs.append("set_ojama", Type.S8, self._row_value(row, "set_ojama", [0] * 3))
        netvs.append("set_recommend", Type.S8, self._row_value(row, "set_recommend", [0] * 3))
        netvs.append("netvs_play_cnt", Type.U32, self._row_value(row, "netvs_play_cnt", 0))
        root.children.append(netvs)

        customize = self._row_value(row, "customize", {})
        if not isinstance(customize, dict):
            customize = {}
        custom = XMLNode.void("customize")
        custom.append("seal_0", Type.U16, customize.get("seal_0", 0))
        custom.append("seal_1", Type.U16, customize.get("seal_1", 0))
        custom.append("seal_2", Type.U16, customize.get("seal_2", 0))
        custom.append("seal_3", Type.U16, customize.get("seal_3", 0))
        custom.append("seal_4", Type.U16, customize.get("seal_4", 0))
        custom.append("seal_5", Type.U16, customize.get("seal_5", 0))
        custom.append("seal_6", Type.U16, customize.get("seal_6", 0))
        custom.append("seat", Type.U16, customize.get("seat", 0))
        custom.append("touch_th", Type.U16, customize.get("touch_th", 0))
        custom.append("lane_cover", Type.U16, customize.get("lane_cover", 0))
        custom.append("stage_bk", Type.U16, customize.get("stage_bk", 0))
        custom.append("highlight", Type.U16, customize.get("highlight", 0))
        root.children.append(custom)

        stamp = XMLNode.void("stamp")
        stamp.append("stamp_id", Type.S16, self._row_value(row, "stamp_id", 0))
        stamp.append("cnt", Type.S16, self._row_value(row, "stamp_cnt", 0))
        root.children.append(stamp)

    def _profile_response(self, row, fresh: bool = False) -> XMLNode:
        root = XMLNode("player")
        root.append("result", Type.S8, 0)
        self._append_profile_sections(root, row, fresh)
        root.attributes["status"] = "0"
        return root

    def _info_response(
        self, root_name: str = "info", include_play_id: bool = False
    ) -> XMLNode:
        root = XMLNode(root_name)
        ranking_info = (
            (2951, 1785110400000, 1785715200000, 748),
            (2950, 1784505600000, 1785110400000, 1739),
            (2949, 1783900800000, 1784505600000, 2196),
            (2948, 1783296000000, 1783900800000, 1596),
            (2947, 1782691200000, 1783296000000, 1704),
            (2946, 1782086400000, 1782691200000, 1518),
            (2945, 1781481600000, 1782086400000, 1522),
            (2944, 1780876800000, 1781481600000, 2078),
            (2943, 1780272000000, 1780876800000, 996),
            (2942, 1779667200000, 1780272000000, 2218),
            (2941, 1779062400000, 1779667200000, 866),
            (2940, 1778457600000, 1779062400000, 2180),
            (2939, 1777852800000, 1778457600000, 207),
            (2938, 1777248000000, 1777852800000, 2105),
            (2937, 1776643200000, 1777248000000, 268),
            (2936, 1776038400000, 1776643200000, 1516),
            (2935, 1775433600000, 1776038400000, 1777),
        )
        popular_characters = (1866, 2495, 577, 2445)
        popular_music = (
            1082, 1027, 1042, 2209, 859, 1230, 1420, 1114, 699, 1854, 1310, 1169,
            1876, 1887, 135, 1641, 1202, 1893, 2331, 795, 883, 929, 1359, 2311,
            2315, 1376, 576, 1795, 2221, 660, 1198, 1250, 1892, 2253, 1824, 2262,
            2327, 1672, 2285, 1208, 1899, 276, 873, 2291, 1211, 88, 1165, 1585,
            89, 1588, 1870, 1368, 1757, 1912, 1171, 1191, 1433, 1616, 2014, 693,
            1482, 148, 1204, 1258, 1495, 1273, 2332, 1160, 1856, 1212, 453, 1868,
            548, 1168, 1217, 1756, 1911, 2150, 107, 557, 1229, 1592, 2207, 108,
            558, 1068, 1593, 1763, 1885, 1919, 2317, 126, 1183, 1233, 1395, 1602,
            1886, 1921, 2214, 2318, 133, 655, 1102, 1244, 1613, 1798, 1922, 2319,
            1192, 1248, 1800, 1888, 1982, 2228, 2321, 145, 672, 1118, 1476, 1801,
            2326, 147, 1120, 1251, 1655, 2016, 1121, 1665, 1830, 1894, 2021, 2263,
            159, 1125, 1205, 1498, 1837, 1895, 2025, 2264, 224, 819, 1127, 1207,
            1276, 1499, 1718, 1845, 1896, 2049, 2334, 269, 1128, 1278, 1500, 1721,
            2050, 2290, 2335, 1129, 1210, 1548, 1730, 1855, 1900, 2099, 346, 1324,
            1553, 1733, 1903, 2106, 2293, 352, 888, 1161, 1353, 1568, 1744, 1861,
            1908, 2110, 2299, 1214, 1358, 1754, 1910, 2147, 2308,
        )
        goods = ((1, 15, 30), (16, 30, 40), (31, 45, 60), (46, 60, 80), (61, 98, 200), (99, 169, 250))

        if include_play_id:
            root.append("play_id", Type.S32, 0)

        def add_phase(event_id: int, phase: int) -> None:
            node = XMLNode.void("phase")
            node.append("event_id", Type.S16, event_id)
            node.append("phase", Type.S16, phase)
            root.children.append(node)

        add_phase(0, 8)
        add_phase(1, 2)
        add_phase(2, 4)
        add_phase(3, 0)
        add_phase(4, 12)
        add_phase(5, 3)
        add_phase(6, 2)
        add_phase(7, 2)
        for course_id, start_date, end_date, music_id in ranking_info:
            node = XMLNode.void("ranking_info")
            node.append("course_id", Type.S16, course_id)
            node.append("start_date", Type.U64, start_date)
            node.append("end_date", Type.U64, end_date)
            node.append("music_id", Type.S32, music_id)
            root.children.append(node)
        for choco_id in range(5):
            node = XMLNode.void("choco")
            node.append("choco_id", Type.S16, choco_id)
            node.append("param", Type.S32, -1)
            root.children.append(node)
        for start, end, price in goods:
            for item_id in range(start, end + 1):
                node = XMLNode.void("goods")
                node.append("item_id", Type.S32, item_id)
                node.append("item_type", Type.S16, 3)
                node.append("price", Type.S32, price)
                node.append("goods_type", Type.S16, 0)
                root.children.append(node)
        for rank, chara_num in enumerate(popular_characters, 1):
            node = XMLNode.void("popular")
            node.append("rank", Type.S16, rank)
            node.append("chara_num", Type.S16, chara_num)
            root.children.append(node)
        for music_num in popular_music:
            node = XMLNode.void("popular_music")
            node.append("music_num", Type.S16, music_num)
            root.children.append(node)
        root.append("license_music", Type.S16, -1)
        root.append("license_music_new", Type.S16, -1)
        for no in range(1, 5):
            node = XMLNode.void("news")
            node.append("no", Type.S16, no)
            node.append("type", Type.U8, 0)
            node.append("image_no", Type.S16, no)
            node.append("title", Type.Str, "popn news thing")
            node.append("main", Type.Str, "idk what this is")
            root.children.append(node)
        root.attributes["status"] = "0"
        return root

    async def handle_pcb_boot(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_error(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_pcb_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb")

    async def handle_info_common(self, request: XMLNode) -> XMLNode:
        return self._info_response()

    async def handle_player_read(self, request: XMLNode) -> XMLNode:
        _, profile = await self._get_profile(request)
        return self._profile_response(profile)

    async def handle_player_new(self, request: XMLNode) -> XMLNode:
        _, profile = await self._get_profile(request)
        fresh = self._row_value(profile, "total_play_cnt", 0) == 0
        return self._profile_response(profile, fresh=fresh)

    async def handle_player_conversion(self, request: XMLNode) -> XMLNode:
        return await self.handle_player_read(request)

    async def handle_player_start(self, request: XMLNode) -> XMLNode:
        user_id, profile = await self._get_profile(request)
        if user_id is not None and profile is not None:
            total = self._row_value(profile, "total_play_cnt", 0)
            today = self._row_value(profile, "today_play_cnt", 0)
            await self.data.profile.update_profile(
                user_id,
                {"total_play_cnt": total + 1, "today_play_cnt": today + 1},
            )
        return self._info_response("player", include_play_id=True)

    async def handle_player_end(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_logout(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_read_option(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    @staticmethod
    def _children(node: Optional[XMLNode], name: str) -> List[XMLNode]:
        if node is None:
            return []
        return [child for child in node.children if child.name == name]

    def _playlog_values(
        self,
        node: XMLNode,
        parent: Optional[XMLNode] = None,
        stage_number: Optional[int] = None,
        profile=None,
    ) -> Dict[str, Any]:
        def value(name: str, default: Any = None) -> Any:
            current = self._value(node, name)
            if current is None and parent is not None:
                current = self._value(parent, name)
            return default if current is None else current

        def parent_value(path: str, default: Any = None) -> Any:
            if parent is None:
                return default
            return self._value(parent, path, default)

        values = {
            "ref_id": value("ref_id"),
            "data_id": value("data_id"),
            # player.write stages do not repeat these values. They live in
            # account/config, except for the player name, which is retained
            # in the profile and omitted from this request entirely.
            "name": value("name", self._row_value(profile, "name")),
            "chara_num": value(
                "chara_num",
                parent_value("config/chara", self._row_value(profile, "chara")),
            ),
            "mode": value(
                "mode",
                parent_value("config/mode", self._row_value(profile, "mode")),
            ),
            "play_id": value("play_id", parent_value("account/play_id")),
            "stage": value("stage", stage_number),
            "music_num": value("music_num", value("no", 0)),
            "sheet_num": value("sheet_num", value("sheet", 0)),
            "clear_type": value("clear_type"),
            "clear_rank": value("clear_rank"),
            "score": value("score"),
            "cool": value("cool"),
            "great": value("great"),
            "good": value("good"),
            "bad": value("bad"),
            "combo": value("combo"),
            "highlight": value("highlight"),
            "gauge": value("gauge"),
            "gauge_type": value("gauge_type"),
            "is_netvs": value("is_netvs"),
            "is_win": value("is_win"),
            "is_image_store": value("is_image_store"),
            "is_option_save": value("is_option_save"),
            "hispeed": value("hispeed"),
            "popkun": value("popkun"),
            "hidden": value("hidden"),
            "hidden_rate": value("hidden_rate"),
            "sudden": value("sudden"),
            "sudden_rate": value("sudden_rate"),
            "randmir": value("randmir"),
            "ojama_0": value("ojama_0"),
            "ojama_1": value("ojama_1"),
            "forever_0": value("forever_0"),
            "forever_1": value("forever_1"),
            "full_setting": value("full_setting"),
            "guide_se": value("guide_se"),
            "guide_se_vol": value("guide_se_vol"),
            "lift": value("lift"),
            "lift_rate": value("lift_rate"),
            "judge_ad": value("judge_ad"),
            "roof": value("roof"),
            "long_pop": value("long_pop"),
            "judge": value("judge"),
            "slow": value("slow"),
            "fast": value("fast"),
            "ex_gauge_lv": value("ex_gauge_lv"),
            "is_super_extra": value("is_super_extra"),
            "netvs_ojama_type": value("netvs_ojama_type"),
            "netvs_type": value("netvs_type"),
            "netvs_rank": value("netvs_rank"),
            "netvs_ojama_0": value("netvs_ojama_0"),
            "netvs_ojama_1": value("netvs_ojama_1"),
            "netvs_ojama_2": value("netvs_ojama_2"),
            "play_date": value("play_date"),
            "select_total_time": value("select_total_time"),
            "select_used_time": value("select_used_time"),
            "select_remain_time": value("select_remain_time"),
            "category": value("category"),
            "sub_category": value("sub_category"),
            "matching": value("matching"),
            "ojama_vs": value("ojama_vs"),
        }
        return {key: value for key, value in values.items() if value is not None}

    async def _save_music(
        self,
        user_id: int,
        node: XMLNode,
        parent: Optional[XMLNode] = None,
        stage_number: Optional[int] = None,
        profile=None,
    ) -> None:
        await self.data.score.put_playlog(
            user_id,
            self._playlog_values(node, parent, stage_number, profile),
        )

    async def handle_player_write_music(self, request: XMLNode) -> XMLNode:
        user_id, profile = await self._get_profile(request)
        node = self._player(request)
        if user_id is not None and node is not None:
            await self._save_music(user_id, node, profile=profile)
            if self._value(node, "is_option_save", 0):
                option_values = {}
                for name in (
                    "hispeed",
                    "popkun",
                    "hidden",
                    "hidden_rate",
                    "sudden",
                    "sudden_rate",
                    "randmir",
                    "gauge_type",
                    "ojama_0",
                    "ojama_1",
                    "forever_0",
                    "forever_1",
                    "full_setting",
                    "judge",
                    "guide_se",
                    "guide_se_vol",
                    "lift",
                    "lift_rate",
                    "judge_ad",
                    "roof",
                    "long_pop",
                ):
                    value = self._value(node, name)
                    if value is not None:
                        option_values[name] = value
                if option_values:
                    await self.data.profile.update_profile(user_id, option_values)
        return XMLNode.void("player")

    async def handle_player_read_score(self, request: XMLNode) -> XMLNode:
        user_id, _ = await self._get_profile(request)
        root = XMLNode("player")
        scores = (
            await self.data.score.get_scores(user_id) if user_id is not None else []
        )
        for record in scores:
            music = XMLNode.void("music")
            for name, type_ in (
                ("music_num", Type.S16),
                ("sheet_num", Type.U8),
                ("score", Type.S32),
                ("clear_type", Type.U8),
                ("score_ver", Type.S32),
                ("clear_type_ver", Type.U8),
                ("clear_rank", Type.U8),
                ("cnt", Type.S16),
            ):
                value = record.get(name, 0)
                if name == "score_ver":
                    value = record.get("score", 0)
                elif name == "clear_type_ver":
                    value = record.get("clear_type", 0)
                music.append(name, type_, value)
            root.children.append(music)
        root.attributes["status"] = "0"
        return root

    async def handle_player_write(self, request: XMLNode) -> XMLNode:
        user_id, profile = await self._get_profile(request)
        node = self._player(request)
        if user_id is None or node is None:
            return XMLNode.void("player")

        values: Dict[str, Any] = {}
        account_fields = (
            "name",
            "tutorial",
            "read_news",
            "latest_music",
            "nice",
            "favorite_chara",
            "popn_class",
            "power_point",
            "power_point_list",
            "sc_news_no",
            "read_policy",
            "language",
        )
        config_fields = (
            "mode",
            "chara",
            "music",
            "sheet",
            "category",
            "sub_category",
            "chara_category",
            "ms_banner_disp",
            "ms_down_info",
            "ms_raise_type",
            "banner_sort",
            "disp_setting",
            "h_vol",
            "hiscore_disp",
            "lane_type",
            "brightness",
            "key_beam",
            "lane_line",
        )
        option_fields = (
            "hispeed",
            "popkun",
            "hidden",
            "hidden_rate",
            "sudden",
            "sudden_rate",
            "randmir",
            "gauge_type",
            "ojama_0",
            "ojama_1",
            "forever_0",
            "forever_1",
            "full_setting",
            "judge",
            "guide_se",
            "guide_se_vol",
            "lift",
            "lift_rate",
            "judge_ad",
            "roof",
            "long_pop",
        )
        for section, fields in (
            ("account", account_fields),
            ("config", config_fields),
            ("option", option_fields),
        ):
            section_node = next(
                (child for child in node.children if child.name == section), None
            )
            for field in fields:
                value = (
                    self._value(section_node, field)
                    if section_node is not None
                    else None
                )
                if value is not None:
                    values[field] = value

        info = next((child for child in node.children if child.name == "info"), None)
        if info is not None and self._value(info, "ep") is not None:
            values["ep"] = self._value(info, "ep")

        customize_node = next(
            (child for child in node.children if child.name == "customize"), None
        )
        if customize_node is not None:
            customization = dict(self._row_value(profile, "customize", {}) or {})
            for child in customize_node.children:
                customization[child.name] = child.value
            values["customize"] = customization

        await self.data.profile.update_profile(user_id, values)
        for stage_number, stage in enumerate(self._children(node, "stage"), 1):
            await self._save_music(user_id, stage, node, stage_number, profile)
        return XMLNode.void("player")

    async def handle_player_friend(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_write_course(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_update_ranking(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_buy(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player")

    async def handle_player_tsumtsum(self, request: XMLNode) -> XMLNode:
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

