from typing import Any, Dict, Iterable, List, Optional

from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import Type, XMLNode

from .config import PopnConfig
from .const import PopnConstants
from .jamfizz import PopnJamFizz


HICHEERS_ITEM_MASK = bytes.fromhex("3df7b7ff4fb9bfe2f7d77af7b7dfdaffffdfffffff7bff3f9fffffffff00000000bcfff8ff1cf8ff0f00e0ff3fb7ffff3f006cbfffaf1fc0fbddfdf8f09fffafeff7f70bffffefffffff27fefffffffffff9fdfffdffffcfffffdffffffff5a7f8fffffffffffcff9fffffffffffffff29f97fffffffffffff02e1fff0ffffffffffffff2ffffffffffffdffff3f80fffffffffffffff7ffcfffffbfffdfffff0000f0ff8fffffdffeffffffffffffffff7ffcffbffffffbd3fffffeffffff0b80feffdbf3fffffffffdffdffffff7fffffffdfffffffffefffffffffffffffdfffffffffbfffffff9fffffffffffefdfffbffffffffffc7fff7ffff27fafffbfff8ffffffffffffffffffffffff27f9ffffffffffffffffffffffffffffbffbfcffffffffffffe73f")


class PopnHiCheers(PopnJamFizz):
    """The M39 Hi~Cheers player protocol.

    Hi~Cheers uses the same card-management services as the earlier Pop'n
    versions, but its player payload is different.  The handlers below keep
    the complete request/response shape from the captured M39 sessions and
    persist the state that is sent by the game.
    """

    PHASES = ((0, 8), (1, 2), (2, 4), (3, 0), (4, 12), (5, 3), (6, 2), (7, 2))
    RANKING_INFO = (
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
    POPULAR_CHARACTERS = (1866, 2495, 577, 2445)
    POPULAR_MUSIC = (
        1082, 1027, 859, 1042, 2209, 1854, 1310, 1230, 1420, 1114, 699,
        883, 929, 1169, 1876, 1887, 135, 1641, 1202, 1893, 2331, 795,
        2285, 1208, 1899, 276, 873, 2291, 1211, 88, 1165, 1585, 1359,
        2311, 2315, 1376, 576, 1795, 2221, 660, 1198, 1250, 1892, 2253,
        1824, 2262, 2327, 1672, 1160, 1856, 1212, 453, 1868, 89, 1588,
        1870, 1368, 1757, 1912, 1171, 1191, 1433, 1616, 2014, 693, 1482,
        148, 1204, 1258, 1495, 1273, 2332, 224, 819, 1127, 1207, 1276,
        1499, 1718, 1845, 1896, 2049, 2334, 269, 1128, 1278, 1500, 1721,
        2050, 2290, 2335, 1129, 1210, 1548, 1730, 1855, 1900, 2099, 346,
        1324, 1553, 1733, 1903, 2106, 2293, 352, 888, 1161, 1353, 1568,
        1744, 1861, 1908, 2110, 2299, 1214, 1358, 1754, 1910, 2147, 2308,
        548, 1168, 1217, 1756, 1911, 2150, 107, 557, 1229, 1592, 2207,
        108, 558, 1068, 1593, 1763, 1885, 1919, 2317, 126, 1183, 1233,
        1395, 1602, 1886, 1921, 2214, 2318, 133, 655, 1102, 1244, 1613,
        1798, 1922, 2319, 1192, 1248, 1800, 1888, 1982, 2228, 2321, 145,
        672, 1118, 1476, 1801, 2326, 147, 1120, 1251, 1655, 2016, 1121,
        1665, 1830, 1894, 2021, 2263, 159, 1125, 1205, 1498, 1837, 1895,
        2025, 2264,
    )
    GOODS = (
        (1, 15, 30), (16, 30, 40), (31, 45, 60),
        (46, 60, 80), (61, 98, 200), (99, 169, 250),
    )
    # Bitset of the item IDs present in the captured M39 player payload.
    ITEM_MASK = HICHEERS_ITEM_MASK
    ITEM_IDS = tuple(
        item_id
        for item_id in range(len(HICHEERS_ITEM_MASK) * 8)
        if HICHEERS_ITEM_MASK[item_id // 8] & (1 << (item_id % 8))
    )

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
    def _value(request: XMLNode, path: str, default: Any = None) -> Any:
        try:
            return request.xpath(path).value
        except Exception:
            return default

    @staticmethod
    def _player(request: XMLNode) -> Optional[XMLNode]:
        return next((child for child in request.children if child.name == "player"), None)

    @staticmethod
    def _row_value(row, key: str, default: Any = None) -> Any:
        if row is None:
            return default
        try:
            value = row._mapping[key]
        except (KeyError, TypeError):
            return default
        return default if value is None else value

    @staticmethod
    def _list(value: Any, default: Iterable[Any]) -> List[Any]:
        if isinstance(value, (list, tuple)):
            return list(value)
        return list(default)

    async def _get_profile(self, request: XMLNode):
        ref_id = self._value(request, "player/ref_id")
        if not ref_id:
            return None, None

        user_id = await self.data.user.get_user_id_by_refid(ref_id)
        if user_id is None:
            return None, None

        profile = await self.data.profile.get_profile(user_id)
        if profile is None:
            name = self._value(request, "player/name", "なし") or "なし"
            pref = self._value(request, "player/pref", 0)
            profile = await self.data.profile.create_profile(user_id, name, pref or 0)

        return user_id, profile

    @staticmethod
    def _append(parent: XMLNode, name: str, type_: Type, value: Any, count: int = None) -> XMLNode:
        attrs = {} if count is None else {"__count": count}
        return parent.append(name, type_, value, **attrs)

    def _append_account(self, root: XMLNode, row, fresh: bool = False) -> None:
        account = XMLNode.void("account")
        defaults = {
            "g_pm_id": "000000000000", "name": "なし", "read_news": 0,
            "nice": [-1] * 100, "favorite_chara": [-1] * 100,
            "power_point": 0, "player_point": 300, "power_point_list": [-1] * 20,
            "tutorial": 0, "is_conv": 0, "latest_music": [-1] * 30,
            "total_play_cnt": 0, "active_fr_num": 0, "popn_class": 0,
            "option_tuto": False, "sc_news_no": 0, "read_policy": 0, "language": 0,
        }
        for key in defaults:
            defaults[key] = self._row_value(row, key, defaults[key])
        if fresh:
            defaults.update({"tutorial": 0, "total_play_cnt": 1, "read_news": 0})

        specs = (
            ("g_pm_id", Type.Str), ("name", Type.Str), ("read_news", Type.S16),
            ("nice", Type.S16), ("favorite_chara", Type.S16), ("power_point", Type.S32),
            ("player_point", Type.S32), ("power_point_list", Type.S32),
            ("tutorial", Type.S16), ("is_conv", Type.S8), ("latest_music", Type.S16),
            ("total_play_cnt", Type.S16), ("active_fr_num", Type.U8),
            ("popn_class", Type.S8), ("option_tuto", Type.Bool),
            ("sc_news_no", Type.S32), ("read_policy", Type.S16), ("language", Type.S8),
        )
        for name, type_ in specs:
            value = defaults[name]
            count = len(value) if isinstance(value, list) else None
            self._append(account, name, type_, value, count)
        root.children.append(account)

    def _append_profile_sections(self, root: XMLNode, row, fresh: bool = False) -> None:
        self._append_account(root, row, fresh)

        eaappli = XMLNode.void("eaappli")
        self._append(eaappli, "relation", Type.S8, -1 if fresh else self._row_value(row, "relation", 1))
        root.children.append(eaappli)

        info = XMLNode.void("info")
        self._append(info, "ep", Type.U16, self._row_value(row, "ep", 0))
        self._append(info, "estatus", Type.U16, 0)
        root.children.append(info)

        config = XMLNode.void("config")
        config_defaults = {
            "mode": 0, "chara": -1, "music": -1, "sheet": 0,
            "category": -1, "sub_category": -1, "chara_category": -1,
            "ms_banner_disp": 0, "ms_down_info": 0, "ms_raise_type": 0,
            "banner_sort": 0, "disp_setting": 0, "h_vol": 0,
            "hiscore_disp": False, "lane_type": 0, "brightness": 0,
            "key_beam": 0, "lane_line": 0,
        }
        if fresh:
            for key in ("ms_banner_disp", "ms_down_info", "ms_raise_type", "banner_sort", "disp_setting", "h_vol", "lane_type", "brightness", "key_beam", "lane_line"):
                config_defaults[key] = -1
        config_types = {
            "mode": Type.U8, "chara": Type.S16, "music": Type.S16, "sheet": Type.U8,
            "category": Type.S8, "sub_category": Type.S8, "chara_category": Type.S8,
            "ms_banner_disp": Type.S8, "ms_down_info": Type.S8, "ms_raise_type": Type.S8,
            "banner_sort": Type.S8, "disp_setting": Type.S8, "h_vol": Type.S8,
            "hiscore_disp": Type.Bool, "lane_type": Type.S8, "brightness": Type.S8,
            "key_beam": Type.S8, "lane_line": Type.S8,
        }
        for name, type_ in config_types.items():
            self._append(config, name, type_, self._row_value(row, name, config_defaults[name]))
        root.children.append(config)

        option = XMLNode.void("option")
        option_defaults = {
            "hispeed": 0 if fresh else 10, "popkun": 0, "hidden": False,
            "hidden_rate": 0 if fresh else -1, "sudden": False,
            "sudden_rate": 0 if fresh else -1, "randmir": 0, "gauge_type": 0,
            "ojama_0": 0, "ojama_1": 0, "forever_0": False, "forever_1": False,
            "full_setting": False if fresh else True, "judge": 0 if fresh else 1,
            "guide_se": 0, "lift": False, "lift_rate": 0 if fresh else -1,
            "judge_ad": 0, "roof": 0, "long_pop": 0,
        }
        option_types = {
            "hispeed": Type.S16, "popkun": Type.U8, "hidden": Type.Bool,
            "hidden_rate": Type.S16, "sudden": Type.Bool, "sudden_rate": Type.S16,
            "randmir": Type.S8, "gauge_type": Type.S8, "ojama_0": Type.U8,
            "ojama_1": Type.U8, "forever_0": Type.Bool, "forever_1": Type.Bool,
            "full_setting": Type.Bool, "judge": Type.U8, "guide_se": Type.S8,
            "lift": Type.Bool, "lift_rate": Type.S16, "judge_ad": Type.S8,
            "roof": Type.S16, "long_pop": Type.S8,
        }
        for name, type_ in option_types.items():
            self._append(option, name, type_, self._row_value(row, name, option_defaults[name]))
        root.children.append(option)

        custom_cate = XMLNode.void("custom_cate")
        for name, value in (("valid", 0), ("lv_min", -1), ("lv_max", -1), ("medal_min", -1), ("medal_max", -1), ("friend_no", -1), ("score_flg", -1)):
            self._append(custom_cate, name, Type.S8, value)
        root.children.append(custom_cate)

        root.children.append(XMLNode.void("navi_data"))

        for item_id in self.ITEM_IDS:
            item = XMLNode.void("item")
            self._append(item, "type", Type.U8, 0)
            self._append(item, "id", Type.U16, item_id)
            self._append(item, "param", Type.U16, 15)
            self._append(item, "is_new", Type.Bool, False)
            self._append(item, "get_time", Type.U64, 0)
            root.children.append(item)

        for mission_id in (140, 213, 95) if fresh else (142, 197, 3):
            mission = XMLNode.void("mission")
            self._append(mission, "mission_id", Type.U32, mission_id)
            self._append(mission, "gauge_point", Type.U32, 0)
            self._append(mission, "mission_comp", Type.U32, 0)
            root.children.append(mission)

        netvs = XMLNode.void("netvs")
        self._append(netvs, "record", Type.S16, self._row_value(row, "netvs_record", [0] * 6), 6)
        for _ in range(6):
            self._append(netvs, "dialog", Type.Str, "")
        self._append(netvs, "ojama_condition", Type.S8, self._row_value(row, "ojama_condition", [0] * 74), 74)
        self._append(netvs, "set_ojama", Type.S8, self._row_value(row, "set_ojama", [0] * 3), 3)
        self._append(netvs, "set_recommend", Type.S8, self._row_value(row, "set_recommend", [0] * 3), 3)
        self._append(netvs, "netvs_play_cnt", Type.U32, self._row_value(row, "netvs_play_cnt", 0))
        root.children.append(netvs)

        customize = self._row_value(row, "customize", {})
        if not isinstance(customize, dict):
            customize = {}
        custom = XMLNode.void("customize")
        for name in ("seal_0", "seal_1", "seal_2", "seal_3", "seal_4", "seal_5", "seal_6", "seat", "touch_th", "lane_cover", "stage_bk", "highlight"):
            self._append(custom, name, Type.U16, customize.get(name, 0))
        root.children.append(custom)

        stamp = XMLNode.void("stamp")
        self._append(stamp, "stamp_id", Type.S16, self._row_value(row, "stamp_id", 0))
        self._append(stamp, "cnt", Type.S16, self._row_value(row, "stamp_cnt", 0))
        root.children.append(stamp)

    def _profile_response(self, row, fresh: bool = False) -> XMLNode:
        root = XMLNode("player")
        self._append(root, "result", Type.S8, 0)
        self._append_profile_sections(root, row, fresh)
        root.attributes["status"] = "0"
        return root

    def _info_response(self, root_name: str = "info", include_play_id: bool = False) -> XMLNode:
        root = XMLNode(root_name)
        if include_play_id:
            self._append(root, "play_id", Type.S32, 0)
        for event_id, phase in self.PHASES:
            node = XMLNode.void("phase")
            self._append(node, "event_id", Type.S16, event_id)
            self._append(node, "phase", Type.S16, phase)
            root.children.append(node)
        for course_id, start_date, end_date, music_id in self.RANKING_INFO:
            node = XMLNode.void("ranking_info")
            self._append(node, "course_id", Type.S16, course_id)
            self._append(node, "start_date", Type.U64, start_date)
            self._append(node, "end_date", Type.U64, end_date)
            self._append(node, "music_id", Type.S32, music_id)
            root.children.append(node)
        for choco_id in range(5):
            node = XMLNode.void("choco")
            self._append(node, "choco_id", Type.S16, choco_id)
            self._append(node, "param", Type.S32, -1)
            root.children.append(node)
        for start, end, price in self.GOODS:
            for item_id in range(start, end + 1):
                node = XMLNode.void("goods")
                self._append(node, "item_id", Type.S32, item_id)
                self._append(node, "item_type", Type.S16, 3)
                self._append(node, "price", Type.S32, price)
                self._append(node, "goods_type", Type.S16, 0)
                root.children.append(node)
        for rank, chara_num in enumerate(self.POPULAR_CHARACTERS, 1):
            node = XMLNode.void("popular")
            self._append(node, "rank", Type.S16, rank)
            self._append(node, "chara_num", Type.S16, chara_num)
            root.children.append(node)
        for music_num in self.POPULAR_MUSIC:
            node = XMLNode.void("popular_music")
            self._append(node, "music_num", Type.S16, music_num)
            root.children.append(node)
        self._append(root, "license_music", Type.S16, -1)
        self._append(root, "license_music_new", Type.S16, -1)
        for no in range(1, 5):
            node = XMLNode.void("news")
            self._append(node, "no", Type.S16, no)
            self._append(node, "type", Type.U8, 0)
            self._append(node, "image_no", Type.S16, no)
            self._append(node, "title", Type.Str, "popn news thing")
            self._append(node, "main", Type.Str, "idk what this is")
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
        return self._profile_response(profile, fresh=True)

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

    def _music_record(self, node: XMLNode, previous: List[Dict[str, Any]]) -> Dict[str, Any]:
        def value(name: str, default: Any = 0) -> Any:
            return self._value(node, name, default)

        music_num = value("music_num", value("no", 0))
        sheet_num = value("sheet_num", value("sheet", 0))
        key = f"{music_num}:{sheet_num}"
        old = next((record for record in previous if record.get("key") == key), None)
        return {
            "key": key,
            "music_num": music_num,
            "sheet_num": sheet_num,
            "score": value("score"),
            "clear_type": value("clear_type"),
            "score_ver": value("score"),
            "clear_type_ver": value("clear_type"),
            "clear_rank": value("clear_rank"),
            "cnt": (old or {}).get("cnt", 0) + 1,
            "detail": {child.name: child.value for child in node.children},
        }

    async def _save_music(self, user_id: int, node: XMLNode) -> None:
        profile = await self.data.profile.get_profile(user_id)
        previous = self._row_value(profile, "scores", [])
        if not isinstance(previous, list):
            previous = []
        record = self._music_record(node, previous)
        scores = [item for item in previous if item.get("key") != record["key"]]
        scores.append(record)
        await self.data.profile.update_profile(user_id, {"scores": scores})

    async def handle_player_write_music(self, request: XMLNode) -> XMLNode:
        user_id, _ = await self._get_profile(request)
        node = self._player(request)
        if user_id is not None and node is not None:
            await self._save_music(user_id, node)
            if self._value(request, "player/is_option_save", 0):
                option_values = {}
                for name in ("hispeed", "popkun", "hidden", "hidden_rate", "sudden", "sudden_rate", "randmir", "ojama_0", "ojama_1", "forever_0", "forever_1", "full_setting", "guide_se", "guide_se_vol", "lift", "lift_rate", "judge_ad", "roof", "long_pop"):
                    value = self._value(node, name)
                    if value is not None:
                        option_values[name] = value
                if option_values:
                    await self.data.profile.update_profile(user_id, option_values)
        return XMLNode.void("player")

    async def handle_player_read_score(self, request: XMLNode) -> XMLNode:
        _, profile = await self._get_profile(request)
        root = XMLNode("player")
        scores = self._row_value(profile, "scores", [])
        if not isinstance(scores, list):
            scores = []
        for record in scores:
            music = XMLNode.void("music")
            for name, type_ in (
                ("music_num", Type.S16), ("sheet_num", Type.U8), ("score", Type.S32),
                ("clear_type", Type.U8), ("score_ver", Type.S32),
                ("clear_type_ver", Type.U8), ("clear_rank", Type.U8), ("cnt", Type.S16),
            ):
                self._append(music, name, type_, record.get(name, 0))
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
            "name", "tutorial", "read_news", "latest_music", "nice", "favorite_chara",
            "popn_class", "power_point", "power_point_list", "sc_news_no", "read_policy", "language",
        )
        config_fields = (
            "mode", "chara", "music", "sheet", "category", "sub_category", "chara_category",
            "ms_banner_disp", "ms_down_info", "ms_raise_type", "banner_sort", "disp_setting",
            "h_vol", "hiscore_disp", "lane_type", "brightness", "key_beam", "lane_line",
        )
        option_fields = (
            "hispeed", "popkun", "hidden", "hidden_rate", "sudden", "sudden_rate", "randmir",
            "gauge_type", "ojama_0", "ojama_1", "forever_0", "forever_1", "full_setting", "judge",
            "guide_se", "guide_se_vol", "lift", "lift_rate", "judge_ad", "roof", "long_pop",
        )
        for section, fields in (("account", account_fields), ("config", config_fields), ("option", option_fields)):
            section_node = next((child for child in node.children if child.name == section), None)
            for field in fields:
                value = self._value(section_node, field) if section_node is not None else None
                if value is not None:
                    values[field] = value

        info = next((child for child in node.children if child.name == "info"), None)
        if info is not None and self._value(info, "ep") is not None:
            values["ep"] = self._value(info, "ep")

        customize_node = next((child for child in node.children if child.name == "customize"), None)
        if customize_node is not None:
            customization = dict(self._row_value(profile, "customize", {}) or {})
            for child in customize_node.children:
                customization[child.name] = child.value
            values["customize"] = customization

        await self.data.profile.update_profile(user_id, values)
        for stage in self._children(node, "stage"):
            await self._save_music(user_id, stage)
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
