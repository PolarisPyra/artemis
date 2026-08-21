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

    FORCE_UNLOCK_SONGS_OPTION = "popn_force_unlock_songs"
    FORCE_UNLOCK_DECO_OPTION = "popn_force_unlock_deco"
    MUSIC_PHASE_OPTION = "popn_music_phase"
    EXTRA_STAGE_PHASE_OPTION = "popn_extra_stage_phase"
    TATAITE_PONPON_PHASE_OPTION = "popn_tataite_ponpon_phase"
    ENABLE_LICENSES_OPTION = "popn_enable_licenses"
    EVENT_PHASES = {
        0: 7,
        1: 1,
        2: 0,
        3: -1,
        4: 0,
        5: 2,
        7: 1,
    }
    LICENSE_MUSIC = (
        1186,
        2272,
        2286,
        2288,
        2289,
        2290,
        2309,
        2312,
        2313,
        2314,
        2316,
        2318,
        2319,
        2320,
        2321,
    )
    # M39's song-eligibility predicate checks every music record carrying
    # mask bit 0x00020000 against the license_music arrays. These four IDs are
    # present in that masked set but absent from the normal live-license list.
    FORCE_UNLOCK_LICENSE_MUSIC = tuple(
        sorted(set(LICENSE_MUSIC).union((670, 2208, 2236, 2257)))
    )
    POPULAR_CHARA = (
        2449, 2502, 2463, 2475, 1879, 2457, 2474, 2495, 2506, 2453,
        2317, 996, 577, 891, 2290, 1892, 2033, 1000, 2437, 1216,
    )
    POPULAR_MUSIC = (748,1089,808,1272,1976,690,1763,1241,1683,1567,1764,2150,2072,1628,1042,1024,1229,89,2025,2028,1110,1741,875,449,1119,1586,1748,1804,1429,1109,2136,1410,1945,1682,1812,1593,1236,1765,2209,1191,2094,781,820,1404,1403,1549,1495,1488,1130,2073,747,1487,1829,2002,1116,1729,1739,1469,1025,2127,1232,223,1270,1271,1430,1349,2071,1364,2162,181,2221,1623,1547,1103,1662,314,1102,888,1085,1346,2111,25,579,417,1718,1746,1044,1214,818,1169,601,1752,1786,1120,1986,1216,388,1525,1031,2137,1598,2118,1003,946,616,1568,1087,1377,1419,1400,1611,1234,2088,1674,1701,1800,1009,1226,1022,2013,2206,1754,1630,1352,0,1944,1728,2049,551,2210,1778,1983,712,1588,1965,1833,962,1604,947,370,354,1731,284,1956,1167,1742,1111,436,1514,1520,1243,1408,1624,1392,561,2016,1923,1388,539,2203,1166,1974,1730,991,1215,754,2160,1698,2096,1158,2015,1310,1326,1795,1788,594,787,2041,967,1561,1714,1187,1484,1165,1197,1548,963,1678,851,1721,1621,1592,188,1127,1703,1803,1794,1750,1112,2158,1801,1096,821,2084,88,1667,846,1209,1168,294,1242,1194,2045,499,1697,699,2108,1964,2017,1104,1321,1164,1507,2107,1065,1892,142,1928,819,2060,373,1677,2117,2087,735,2021,1200,1737,172,2076,822,341,171,912,1952,668,1126,487,1399,663,1267,871,2126,1028,147,1196,2047,1426,1049,1506,1726,1563,2079,215,115,1874,1186,1307,1876,1978,1798,1444,1827,1917,1749,1725,2099,1438,1862,1039,1589,670,1008,1811,2014,1244,1617,1521,1250,1263,1524,2115,1747,1848,2101,1824,1114,1515,1796,1898,645,697,1505,148,1001,1207,1733,1360,1550,938,945,2185,869,1401,752,2106,2089,1922,1185,1047,823,1012,1808,353,1046,2123,1118,1977,1450,985,1834,2030,655,1650,1370,1324,1569,1670,2082,1368,1906,1080,2061,1037,1946,1830,1276,2066,833,1576,882,618,1607,1359,374,1357,1625,1814,1787,1890,572,1522,1551,1992,2144,567,125,1014,743,2207,2213,1010,187,1545,1602,1402,1679,1656,1823,1499,1676,2146,809,195,1350,1021,1433,1668,1774,2009,2184,1231,95,320,1190,2211,647,684,1380,1351,2095,1279,810,692,1245,803,1391,1653,1704,2128,1988,1381,285,1160,1091,847,421,1064,1546,2008,877,999,1777,1311,1870,1325,2193,2114,723,1990,1264,620,1239,1128,1202,784,1953,2238,660,836,1850,1492,491,1768,1708,1694,675,646,778,1732,534,943,1354,1825,43,1206,1664,1179,1555,1695,1378,1033,1210,1319,914,857,1756,1789,2152,2027,2093,1987,983,705,1646,1212,1171,1799,1575,795,1680,2018,577,2086,1641,936,1663,1322,1775,1412,1633,1414,2138,680,874,1880,2256,1417,1266,1390)
    # These High☆Cheers song IDs are present in Tablanbass's force-unlock
    # response but are absent from the imported static chart table.
    FORCE_UNLOCK_CATALOG_GAPS = (
        1, 6, 7, 11, 19, 22, 36, 37, 39, 41, 42, 46, 54, 56, 58, 59,
        60, 67, 75, 77, 80, 82, 87, 91, 99, 102, 109, 112, 114, 117,
        141, 175, 190, 198, 232, 233, 234, 236, 237, 238, 239, 240,
        241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252,
        253, 254, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265,
        270, 280, 281, 282, 296, 297, 301, 302, 303, 304, 305, 306,
        324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335,
        336, 337, 338, 339, 340, 358, 359, 363, 366, 390, 391, 392,
        393, 394, 395, 396, 397, 398, 399, 400, 401, 404, 407, 414,
        428, 430, 437, 438, 439, 440, 441, 442, 443, 444, 445, 450,
        457, 461, 465, 472, 473, 474, 480, 481, 482, 493, 494, 508,
        510, 516, 523, 531, 538, 540, 541, 542, 543, 564, 595, 596,
        598, 599, 600, 657, 673, 700, 701, 725, 753, 755, 763, 764,
        766, 768, 769, 770, 816, 817, 837, 838, 897, 898, 900, 902,
        903, 905, 906, 919, 1912, 1929, 2149, 5171,
    )

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
        player = self._player(request)
        ref_id = player.attributes.get("ref_id") if player is not None else None
        if not ref_id:
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
        else:
            profile = await self.data.profile.ensure_g_pm_id(user_id, profile)

        return user_id, profile

    async def _get_option(self, user_id: Optional[int], key: str, default: int) -> int:
        if user_id is None:
            return default
        value = await self.data.cozynet.get_option(user_id, key)
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    async def _get_setting_user_id(self, fallback: Optional[int] = None) -> Optional[int]:
        owner_id = await self.data.arcade.get_machine_owner(self.protocol.pcbid)
        return owner_id if owner_id is not None else fallback

    def _append_account(self, root: XMLNode, row, fresh: bool = False) -> None:
        account = XMLNode.void("account")
        account.append("g_pm_id", Type.Str, self._row_value(row, "g_pm_id", "000000000000"))
        account.append("name", Type.Str, self._row_value(row, "name", "なし"))
        account.append("area_id", Type.S16, self._row_value(row, "area_id", 0))
        account.append("use_navi", Type.S16, self._row_value(row, "use_navi", 1))
        account.append("read_news", Type.S16, 0 if fresh else self._row_value(row, "read_news", 0))
        nice = list(self._row_value(row, "nice", []))
        favorite_chara = list(self._row_value(row, "favorite_chara", []))
        special_area = list(self._row_value(row, "special_area", []))
        chocolate_charalist = list(self._row_value(row, "chocolate_charalist", []))
        account.append("nice", Type.S16, (nice + [-1] * 100)[:100])
        account.append("favorite_chara", Type.S16, (favorite_chara + [-1] * 20)[:20])
        account.append("special_area", Type.S16, (special_area + [0] * 8)[:8])
        account.append("chocolate_charalist", Type.S16, (chocolate_charalist + [-1] * 5)[:5])
        account.append("chocolate_sp_chara", Type.S32, self._row_value(row, "chocolate_sp_chara", 0))
        account.append("chocolate_pass_cnt", Type.S32, self._row_value(row, "chocolate_pass_cnt", 0))
        account.append("chocolate_hon_cnt", Type.S32, self._row_value(row, "chocolate_hon_cnt", 0))
        teacher_setting = list(self._row_value(row, "teacher_setting", []))
        account.append("teacher_setting", Type.S16, (teacher_setting + [-1] * 10)[:10])
        account.append("welcom_pack", Type.Bool, self._row_value(row, "welcom_pack", False))
        account.append("ranking_node", Type.S32, self._row_value(row, "ranking_node", 0))
        account.append("chara_ranking_kind_id", Type.S32, self._row_value(row, "chara_ranking_kind_id", 0))
        account.append("navi_evolution_flg", Type.S8, self._row_value(row, "navi_evolution_flg", 1))
        account.append("ranking_news_last_no", Type.S32, self._row_value(row, "ranking_news_last_no", 0))
        account.append("power_point", Type.S32, self._row_value(row, "power_point", 0))
        account.append("player_point", Type.S32, self._row_value(row, "player_point", 0))
        power_point_list = list(self._row_value(row, "power_point_list", []))
        account.append("power_point_list", Type.S32, (power_point_list + [-1] * 20)[:20])
        account.append("tutorial", Type.S16, self._row_value(row, "tutorial", 1))
        account.append("staff", Type.S8, self._row_value(row, "staff", 0))
        account.append("item_type", Type.S16, self._row_value(row, "item_type", 0))
        account.append("item_id", Type.S16, self._row_value(row, "item_id", 0))
        account.append("is_conv", Type.S8, self._row_value(row, "is_conv", -1))
        license_data = list(self._row_value(row, "license_data", []))
        my_best = list(self._row_value(row, "my_best", []))
        latest_music = list(self._row_value(row, "latest_music", []))
        account.append("license_data", Type.S16, (license_data + [-1] * 20)[:20])
        account.append("my_best", Type.S16, (my_best + [-1] * 20)[:20])
        account.append("latest_music", Type.S16, (latest_music + [-1] * 10)[:10])
        account.append("total_play_cnt", Type.S16, 1 if fresh else self._row_value(row, "total_play_cnt", 0))
        account.append("today_play_cnt", Type.S16, self._row_value(row, "today_play_cnt", 0))
        account.append("consecutive_days", Type.S16, self._row_value(row, "consecutive_days", 0))
        account.append("total_days", Type.S16, self._row_value(row, "total_days", 0))
        account.append("interval_day", Type.S16, self._row_value(row, "interval_day", 0))
        account.append("active_fr_num", Type.U8, self._row_value(row, "active_fr_num", 0))
        account.append("popn_class", Type.S8, self._row_value(row, "popn_class", 1))
        root.children.append(account)

    def _append_static_items(self, root: XMLNode) -> None:
        item_ids = (
            2171, 2330, 2329, 2168, 2338, 2339, 2165, 2358, 2359, 2369,
            2370, 2371, 2353, 2352, 2354, 2324, 2325, 2292, 2334, 2335,
            2342, 2343, 2347, 2348, 2349, 2350, 2351, 2360, 2361, 2362,
            2356, 2357, 2372, 2373, 2303, 2296, 2340, 0,
        )
        for item_id in item_ids:
            item = XMLNode.void("item")
            item.append("type", Type.U8, 0)
            item.append("id", Type.U16, item_id)
            item.append("param", Type.U16, 15)
            item.append("is_new", Type.Bool, False)
            item.append("get_time", Type.U64, 0)
            root.children.append(item)

    async def _append_force_unlocked_songs(self, root: XMLNode) -> None:
        songs = await self.data.static.get_music(self.version)
        if songs is None:
            return

        existing_item_ids = set()
        for child in root.children:
            if child.name != "item":
                continue
            try:
                existing_item_ids.add(int(child.xpath("id").value))
            except (AttributeError, TypeError, ValueError):
                continue

        for song_id in sorted(
            {
                int(self._row_value(song, "songId"))
                for song in songs
                if self._row_value(song, "songId") is not None
            }.union(self.FORCE_UNLOCK_CATALOG_GAPS)
        ):
            if song_id in existing_item_ids:
                continue

            item = XMLNode.void("item")
            item.append("type", Type.U8, 0)
            item.append("id", Type.U16, song_id)
            item.append("param", Type.U16, 15)
            item.append("is_new", Type.Bool, False)
            item.append("get_time", Type.U64, 0)
            root.children.append(item)
            existing_item_ids.add(song_id)

    def _append_force_unlocked_deco(self, root: XMLNode) -> None:
        for deco_id in range(1, 170):
            item = XMLNode.void("item")
            item.append("type", Type.U8, 7)
            item.append("id", Type.U16, deco_id)
            item.append("param", Type.U16, 0)
            item.append("is_new", Type.Bool, False)
            item.append("get_time", Type.U64, 0)
            root.children.append(item)

    def _append_missions(self, root: XMLNode, fresh: bool) -> None:
        mission_ids = (42, 117, 192)
        for mission_id in mission_ids:
            mission = XMLNode.void("mission")
            mission.append("mission_id", Type.U32, mission_id)
            mission.append("gauge_point", Type.U32, 0)
            mission.append("mission_comp", Type.U32, 0)
            root.children.append(mission)

    def _append_event_p29(self, root: XMLNode) -> None:
        event = XMLNode.void("event_p29")
        root.children.append(event)

    def _append_chara_params(self, root: XMLNode) -> None:
        for chara_id in range(56):
            chara = XMLNode.void("chara_param_old")
            chara.append("chara_id", Type.U16, chara_id)
            chara.append("friendship", Type.U16, 0)
            root.children.append(chara)

    def _append_navi_data(self, root: XMLNode) -> None:
        navi_data = XMLNode.void("navi_data")
        navi_data.append("raisePoint", Type.S32, [0] * 5)
        for navi_id in range(13):
            navi = XMLNode.void("navi_param")
            navi.append("navi_id", Type.U16, navi_id)
            navi.append("friendship", Type.S32, 0)
            navi_data.children.append(navi)
        root.children.append(navi_data)

    def _append_netvs(self, root: XMLNode, row) -> None:
        netvs = XMLNode.void("netvs")
        netvs.append("record", Type.S16, self._row_value(row, "netvs_record", [0] * 6))
        for dialog in self._row_value(row, "netvs_dialog", [""] * 6):
            netvs.append("dialog", Type.Str, dialog)
        netvs.append("ojama_condition", Type.S8, self._row_value(row, "ojama_condition", [0] * 74))
        netvs.append("set_ojama", Type.S8, self._row_value(row, "set_ojama", [0] * 3))
        netvs.append("set_recommend", Type.S8, self._row_value(row, "set_recommend", [0] * 3))
        netvs.append("netvs_play_cnt", Type.U32, self._row_value(row, "netvs_play_cnt", 0))
        root.children.append(netvs)

    def _append_customize(self, root: XMLNode, row) -> None:
        customize = self._row_value(row, "customize", {})
        customize = customize if isinstance(customize, dict) else {}
        custom = XMLNode.void("customize")
        for field in ("effect_left", "effect_center", "effect_right", "hukidashi", "comment_1", "comment_2"):
            custom.append(field, Type.U16, self._row_value(row, field, 0))
        for field in (
            "seal_0", "seal_1", "seal_2", "seal_3", "seal_4", "seal_5",
            "seal_6", "seat", "touch_th", "lane_cover", "stage_bk", "highlight",
        ):
            custom.append(field, Type.U16, customize.get(field, 0))
        root.children.append(custom)

    def _append_stamp(self, root: XMLNode, row) -> None:
        stamp = XMLNode.void("stamp")
        stamp.append("stamp_id", Type.S16, self._row_value(row, "stamp_id", 0))
        stamp.append("cnt", Type.S16, self._row_value(row, "stamp_cnt", 0))
        root.children.append(stamp)

    async def _append_profile_sections(
        self, root: XMLNode, row, user_id: int, fresh: bool = False
    ) -> None:
        self._append_account(root, row, fresh)

        eaappli = XMLNode.void("eaappli")
        eaappli.append("relation", Type.S8, 1)
        root.children.append(eaappli)

        info = XMLNode.void("info")
        info.append("ep", Type.U16, self._row_value(row, "ep", 0))
        root.children.append(info)

        config = XMLNode.void("config")
        config.append("mode", Type.U8, self._row_value(row, "mode", 0))
        config.append("chara", Type.S16, self._row_value(row, "chara", -1))
        config.append("music", Type.S16, self._row_value(row, "music", -1))
        config.append("sheet", Type.U8, self._row_value(row, "sheet", 0))
        config.append("category", Type.S8, self._row_value(row, "category", -1))
        config.append("sub_category", Type.S8, self._row_value(row, "sub_category", -1))
        config.append("chara_category", Type.S8, self._row_value(row, "chara_category", -1))
        config.append("course_id", Type.S16, self._row_value(row, "course_id", 0))
        config.append("course_folder", Type.S8, self._row_value(row, "course_folder", 0))
        config.append("ms_banner_disp", Type.S8, -1 if fresh else self._row_value(row, "ms_banner_disp", 0))
        config.append("ms_down_info", Type.S8, -1 if fresh else self._row_value(row, "ms_down_info", 0))
        config.append("ms_side_info", Type.S8, self._row_value(row, "ms_side_info", 3))
        config.append("ms_raise_type", Type.S8, -1 if fresh else self._row_value(row, "ms_raise_type", 0))
        config.append("ms_rnd_type", Type.S8, self._row_value(row, "ms_rnd_type", 0))
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
        option.append("guide_se_vol", Type.U8, self._row_value(row, "guide_se_vol", 3))
        option.append("judge_ad", Type.S8, self._row_value(row, "judge_ad", 0))
        option.append("roof", Type.S16, self._row_value(row, "roof", 0))
        option.append("long_pop", Type.S8, int(self._row_value(row, "long_pop", 0)))
        root.children.append(option)

        custom_cate = XMLNode.void("custom_cate")
        custom_cate.append("valid", Type.S8, self._row_value(row, "custom_valid", 0))
        custom_cate.append("lv_min", Type.S8, self._row_value(row, "custom_lv_min", -1))
        custom_cate.append("lv_max", Type.S8, self._row_value(row, "custom_lv_max", -1))
        custom_cate.append("medal_min", Type.S8, self._row_value(row, "custom_medal_min", -1))
        custom_cate.append("medal_max", Type.S8, self._row_value(row, "custom_medal_max", -1))
        custom_cate.append("friend_no", Type.S8, self._row_value(row, "custom_friend_no", -1))
        custom_cate.append("score_flg", Type.S8, self._row_value(row, "custom_score_flg", -1))
        root.children.append(custom_cate)

        self._append_navi_data(root)

        setting_user_id = await self._get_setting_user_id(user_id)
        force_unlock_songs = await self._get_option(
            setting_user_id, self.FORCE_UNLOCK_SONGS_OPTION, 1
        )
        if force_unlock_songs != 0:
            await self._append_force_unlocked_songs(root)
        else:
            self._append_static_items(root)

        force_unlock_deco = await self._get_option(
            setting_user_id, self.FORCE_UNLOCK_DECO_OPTION, 1
        )
        if force_unlock_deco != 0:
            self._append_force_unlocked_deco(root)
        self._append_chara_params(root)
        self._append_missions(root, fresh)
        self._append_netvs(root, row)
        self._append_customize(root, row)
        self._append_stamp(root, row)
        self._append_event_p29(root)

    async def _profile_response(
        self, row, user_id: int, fresh: bool = False
    ) -> XMLNode:
        root = XMLNode("player24", attributes={"status": "0"})
        root.append("result", Type.S8, 0)
        await self._append_profile_sections(root, row, user_id, fresh)
        return root

    def _info_response(
        self,
        root_name: str = "info24",
        include_play_id: bool = False,
        music_phase: int = 7,
        extra_stage_phase: int = 0,
        tataite_ponpon_phase: int = 0,
        enable_licenses: bool = True,
        force_unlock_songs: bool = False,
    ) -> XMLNode:
        root = XMLNode(root_name)
        if include_play_id:
            root.append("play_id", Type.S32, 0)

        phases = {
            **self.EVENT_PHASES,
            0: music_phase,
            2: extra_stage_phase,
            4: tataite_ponpon_phase,
        }
        for event_id, phase_value in phases.items():
            node = XMLNode.void("phase")
            node.append("event_id", Type.S16, event_id)
            node.append("phase", Type.S16, phase_value)
            root.children.append(node)

        for choco_id in range(5):
            choco = XMLNode.void("choco")
            choco.append("choco_id", Type.S16, choco_id)
            choco.append("param", Type.S32, -1)
            root.children.append(choco)

        goods_prices = (
            (1, 15, 30),
            (16, 30, 40),
            (31, 45, 60),
            (46, 60, 80),
            (61, 98, 200),
            (99, 169, 250),
        )
        for first_id, last_id, price in goods_prices:
            for item_id in range(first_id, last_id + 1):
                goods = XMLNode.void("goods")
                goods.append("item_id", Type.S32, item_id)
                goods.append("item_type", Type.S16, 3)
                goods.append("price", Type.S32, price)
                goods.append("goods_type", Type.S16, 0)
                root.children.append(goods)

        for rank, chara_num in enumerate(self.POPULAR_CHARA, start=1):
            popular = XMLNode.void("popular")
            popular.append("rank", Type.S16, rank)
            popular.append("chara_num", Type.S16, chara_num)
            root.children.append(popular)

        for music_num in self.POPULAR_MUSIC:
            popular_music = XMLNode.void("popular_music")
            popular_music.append("music_num", Type.S16, music_num)
            root.children.append(popular_music)

        if force_unlock_songs:
            force_licenses = list(self.FORCE_UNLOCK_LICENSE_MUSIC)
            root.append("license_music", Type.S16, force_licenses)
            root.append("license_music_new", Type.S16, force_licenses)
        elif enable_licenses:
            root.append("license_music", Type.S16, list(self.LICENSE_MUSIC))
        return root

    async def handle_pcb_boot(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb24", status="0")

    async def handle_pcb_error(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb24", status="0")

    async def handle_pcb_write(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("pcb24", status="0")

    async def handle_info_common(self, request: XMLNode) -> XMLNode:
        setting_user_id = await self._get_setting_user_id()
        return await self._configured_info_response(setting_user_id)

    async def _configured_info_response(
        self, setting_user_id: Optional[int], root_name: str = "info24", include_play_id: bool = False
    ) -> XMLNode:
        music_phase = await self._get_option(setting_user_id, self.MUSIC_PHASE_OPTION, 7)
        extra_stage_phase = await self._get_option(
            setting_user_id, self.EXTRA_STAGE_PHASE_OPTION, 0
        )
        tataite_ponpon_phase = await self._get_option(
            setting_user_id, self.TATAITE_PONPON_PHASE_OPTION, 0
        )
        enable_licenses = (
            await self._get_option(setting_user_id, self.ENABLE_LICENSES_OPTION, 1) != 0
        )
        force_unlock_songs = (
            await self._get_option(
                setting_user_id, self.FORCE_UNLOCK_SONGS_OPTION, 1
            )
            != 0
        )
        return self._info_response(
            root_name,
            include_play_id=include_play_id,
            music_phase=music_phase,
            extra_stage_phase=extra_stage_phase,
            tataite_ponpon_phase=tataite_ponpon_phase,
            enable_licenses=enable_licenses,
            force_unlock_songs=force_unlock_songs,
        )

    async def handle_player_read(self, request: XMLNode) -> XMLNode:
        ref_id = self._value(request, "player/ref_id")
        user_id = await self.data.user.get_user_id_by_refid(ref_id) if ref_id else None
        existing = (
            await self.data.profile.get_profile_data(user_id)
            if user_id is not None
            else None
        )
        _, profile = await self._get_profile(request)
        if (
            user_id is not None
            and existing is not None
            and self._row_value(profile, "total_play_cnt", 0) <= 1
        ):
            migration = {"total_play_cnt": 2, "tutorial": 0, "sc_news_no": 2951}
            await self.data.profile.update_profile(user_id, migration)
            profile = {**profile, **migration}
        return await self._profile_response(profile, user_id)

    async def handle_player_new(self, request: XMLNode) -> XMLNode:
        ref_id = self._value(request, "player/ref_id")
        user_id = await self.data.user.get_user_id_by_refid(ref_id) if ref_id else None
        existing = (
            await self.data.profile.get_profile_data(user_id)
            if user_id is not None
            else None
        )
        _, profile = await self._get_profile(request)
        return await self._profile_response(profile, user_id, fresh=existing is None)

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
        setting_user_id = await self._get_setting_user_id(user_id)
        return await self._configured_info_response(
            setting_user_id, "player24", include_play_id=True
        )

    async def handle_player_end(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_logout(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_read_option(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

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
        return XMLNode.void("player24", status="0")

    def _score_response(self, scores) -> XMLNode:
        root = XMLNode("player24")
        for record in scores:
            music = XMLNode.void("music")
            for name, type_ in (
                ("music_num", Type.S16),
                ("sheet_num", Type.U8),
                ("score", Type.S32),
                ("clear_type", Type.U8),
                ("clear_rank", Type.U8),
                ("cnt", Type.S16),
            ):
                value = record.get(name, 0)
                music.append(name, type_, value)
            root.children.append(music)
        root.attributes["status"] = "0"
        return root

    async def handle_player_read_score(self, request: XMLNode) -> XMLNode:
        user_id, _ = await self._get_profile(request)
        scores = await self.data.score.get_scores(user_id) if user_id is not None else []
        return self._score_response(scores)

    async def handle_player_write(self, request: XMLNode) -> XMLNode:
        user_id, profile = await self._get_profile(request)
        node = self._player(request)
        if user_id is None or node is None:
            return XMLNode.void("player24", status="0")

        values: Dict[str, Any] = {}
        account_fields = (
            "name",
            "tutorial",
            "read_news",
            "latest_music",
            "total_play_cnt",
            "today_play_cnt",
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
        return XMLNode.void("player24", status="0")

    async def handle_player_friend(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_write_course(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_update_ranking(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_buy(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

    async def handle_player_tsumtsum(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("player24", status="0")

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
