from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
    LinkedVerseUnlockConditionType,
    MapAreaConditionLogicalOperator,
    MapAreaConditionType,
)

from .xverse import ChuniXVerse, add_linked_gate_opened_by_map, generate_course_levels


class ChuniXVerseX(ChuniXVerse):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_X_VERSE_X

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.45.00"
        return user_data

    async def handle_get_game_map_area_condition_api_request(self, data: Dict) -> Dict:
        map_area_condition_list = []
        events = await self.data.static.get_enabled_events(self.version)

        if events is None:
            return {
                "length": len(map_area_condition_list),
                "gameMapAreaConditionList": map_area_condition_list,
            }

        events_by_id = {event["eventId"]: event for event in events}

        # The Mystic Rainbow of X-VERSE-X map unlocks when any mainline X-VERSE-X maps are completed.
        mystic_area_1_conditions = {
            "mapAreaId": 3232001,
            "length": 0,
            "mapAreaConditionList": [],
        }
        mystic_area_1_added = False

        def add_mystic_area_condition(
            map_flag_event_id: int, map_id: int, mystic_area_id: int
        ):
            nonlocal mystic_area_1_added
            nonlocal mystic_area_1_conditions
            nonlocal map_area_condition_list
            nonlocal events_by_id

            if (event := events_by_id.get(map_flag_event_id)) is None:
                return

            condition = {
                "type": MapAreaConditionType.MAP_CLEARED.value,
                "conditionId": map_id,
                "logicalOpe": MapAreaConditionLogicalOperator.OR.value,
                "startDate": event["startDate"]
                .replace(hour=0, minute=0, second=0)
                .strftime(self.date_time_format),
                "endDate": "2099-12-31 00:00:00",
            }

            if not mystic_area_1_added:
                map_area_condition_list.append(mystic_area_1_conditions)
                mystic_area_1_added = True

            mystic_area_1_conditions["length"] += 1
            mystic_area_1_conditions["mapAreaConditionList"].append(condition)

            map_area_condition_list.append(
                {
                    "mapAreaId": mystic_area_id,
                    "length": 1,
                    "mapAreaConditionList": [condition],
                }
            )

        add_mystic_area_condition(18080, 3020810, 3232002)
        add_mystic_area_condition(18405, 3020811, 3232003)
        add_mystic_area_condition(18552, 3020812, 3232004)
        add_mystic_area_condition(18682, 3020813, 3232005)

        # Secret AREA: LUMINOUS: Obtain the "MISSION still in progress" title by getting
        # 100pt from カイナン・メルヴィアス's CHUNITHM mission
        if secret_area_luminous_flag := events_by_id.get(18559):
            start_date = (
                secret_area_luminous_flag["startDate"]
                .replace(hour=0, minute=0, second=0)
                .strftime(self.date_time_format)
            )
            condition = {
                "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                "conditionId": 10122,
                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                "startDate": start_date,
                # TODO: base this on the next CMission flag, similar to MISSION in progress
                # in LUMINOUS
                "endDate": "2099-12-31 00:00:00",
            }

            map_area_condition_list.extend(
                {"mapAreaId": map_area_id, "length": 1, "condition": [condition]}
                for map_area_id in (3232101, 3232102)
            )

        return {
            "length": len(map_area_condition_list),
            "gameMapAreaConditionList": map_area_condition_list,
        }

    async def handle_get_game_course_level_api_request(self, data: Dict) -> Dict:
        events = await self.data.static.get_enabled_events(self.version)

        if events is None:
            return {"length": 0, "gameCourseLevelList": []}

        events_by_id = {event["eventId"]: event for event in events}
        course_level_list = []

        if gate_origin := events_by_id.get(17042):
            start_date = gate_origin["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500001, 500002, 500003, 500004, 500005],
                    self.date_time_format,
                )
            )

        if gate_air := events_by_id.get(17106):
            start_date = gate_air["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500101, 500102, 500103, 500104, 500105],
                    self.date_time_format,
                )
            )

        if gate_star := events_by_id.get(17210):
            start_date = gate_star["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500201, 500202, 500203, 500204, 500205],
                    self.date_time_format,
                )
            )

        if gate_amazon := events_by_id.get(17306):
            start_date = gate_amazon["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500301, 500302, 500303, 500304, 500305],
                    self.date_time_format,
                )
            )

        if gate_crystal := events_by_id.get(17409):
            start_date = gate_crystal["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500401, 500402, 500403, 500404, 500405],
                    self.date_time_format,
                )
            )

        if gate_paradise := events_by_id.get(17485):
            start_date = gate_paradise["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500501, 500502, 500503, 500504, 500505],
                    self.date_time_format,
                )
            )

        if gate_new := events_by_id.get(18081):
            start_date = gate_new["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500601, 500602, 500603, 500604, 500605],
                    self.date_time_format,
                )
            )

        if gate_sun := events_by_id.get(18406):
            start_date = gate_sun["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500701, 500702, 500703, 500704, 500705],
                    self.date_time_format,
                )
            )

        if gate_luminous := events_by_id.get(18553):
            start_date = gate_luminous["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500801, 500802, 500803, 500804, 500805],
                    self.date_time_format,
                )
            )

        if gate_verse := events_by_id.get(18683):
            start_date = gate_verse["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [500901, 500902, 500903, 500904, 500905],
                    self.date_time_format,
                )
            )

        if gate_xverse := events_by_id.get(18685):
            start_date = gate_xverse["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [501001, 501002, 501003, 501004, 501005],
                    self.date_time_format,
                )
            )

        if gate_reverse := events_by_id.get(18684):
            start_date = gate_reverse["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [501101, 501102, 501103, 501104, 501105, 501106],
                    self.date_time_format,
                )
            )

        if gate_universe := events_by_id.get(18686):
            start_date = gate_universe["startDate"].replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=None
            )

            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [501201, 501202, 501203, 501204, 501205, 501206],
                    self.date_time_format,
                )
            )
            course_level_list.append(
                generate_course_levels(
                    start_date,
                    [501301, 501302, 501303, 501304, 501305, 501306],
                    self.date_time_format,
                )
            )

        return {
            "length": len(course_level_list),
            "gameCourseLevelList": course_level_list,
        }

    async def handle_get_game_l_v_condition_open_api_request(self, data: Dict) -> Dict:
        events = await self.data.static.get_enabled_events(self.version)

        if events is None:
            return {
                "length": 0,
                "gameLinkedVerseConditionOpenList": [],
            }

        events_by_id = {event["eventId"]: event for event in events}
        conditions = []

        # Linked GATE ORIGIN - VERSE ep. ORIGIN
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17042, 10001, 3020803, self.date_time_format
        )

        # Linked GATE AIR - VERSE ep. AIR
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17106, 10002, 3020804, self.date_time_format
        )

        # Linked GATE STAR - VERSE ep. STAR
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17210, 10003, 3020805, self.date_time_format
        )

        # Linked GATE AMAZON - VERSE ep. AMAZON
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17306, 10004, 3020806, self.date_time_format
        )

        # Linked GATE CRYSTAL - VERSE ep. CRYSTAL
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17409, 10005, 3020807, self.date_time_format
        )

        # Linked GATE PARADISE - VERSE ep. PARADISE
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 17485, 10006, 3020808, self.date_time_format
        )

        # Linked GATE NEW - VERSE ep. NEW
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 18081, 10007, 3020810, self.date_time_format
        )

        # Linked GATE SUN - VERSE ep. SUN
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 18406, 10008, 3020811, self.date_time_format
        )

        # Linked GATE LUMINOUS - VERSE ep. LUMINOUS
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 18553, 10009, 3020812, self.date_time_format
        )

        # Linked GATE VERSE - VERSE ep. VERSE
        add_linked_gate_opened_by_map(
            conditions, events_by_id, 18683, 10010, 3020813, self.date_time_format
        )

        # Clear all 10 Linked GATEs from ORIGIN to VERSE
        if gate_xverse := events_by_id.get(18685):
            start_date = gate_xverse["startDate"].strftime(self.date_time_format)

            conditions.append(
                {
                    "linkedVerseId": 10011,
                    "length": 10,
                    "conditionList": [
                        {
                            "type": 31,
                            "conditionId": condition_id,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 23:59:59",
                        }
                        for condition_id in range(10001, 10011)
                    ],
                }
            )

        if gate_reverse := events_by_id.get(18684):
            conditions.append(
                {
                    "linkedVerseId": 10012,
                    "length": len(range(2968, 2979)),
                    "conditionList": [
                        {
                            "type": 10,
                            "conditionId": condition_id,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_reverse["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 23:59:59",
                        }
                        for condition_id in range(2968, 2979)
                    ],
                }
            )

        if gate_universe := events_by_id.get(18686):
            start_date = gate_universe["startDate"].strftime(self.date_time_format)

            conditions.append(
                {
                    "linkedVerseId": 10013,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": 31,
                            "conditionId": 10012,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_universe["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 23:59:59",
                        }
                    ],
                }
            )
            conditions.append(
                {
                    "linkedVerseId": 10014,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": 31,
                            "conditionId": 10013,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_universe["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 23:59:59",
                        }
                    ],
                }
            )

        return {
            "length": len(conditions),
            "gameLinkedVerseConditionOpenList": conditions,
        }

    async def handle_get_game_l_v_condition_unlock_api_request(
        self, data: Dict
    ) -> Dict:
        events = await self.data.static.get_enabled_events(self.version)

        if events is None:
            return {
                "length": 0,
                "gameLinkedVerseConditionUnlockList": [],
            }

        events_by_id = {event["eventId"]: event for event in events}
        conditions = []

        if gate_origin := events_by_id.get(17042):
            conditions.append(
                {
                    "linkedVerseId": 10001,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.PLAY_SONGS.value,
                            "conditionList": "59;79;148;71;75;140;163;80;51;64;65;74;95;67;53;100;108;107;105;82;76;141;63;147;69;151;70;101;152;180",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_origin["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_air := events_by_id.get(17106):
            conditions.append(
                {
                    "linkedVerseId": 10002,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.COURSE_CLEAR_AND_CLASS_EMBLEM.value,
                            "conditionList": "1_2_3_4_5_6",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_air["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_star := events_by_id.get(17210):
            conditions.append(
                {
                    "linkedVerseId": 10003,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.TROPHY_OBTAINED.value,
                            "conditionList": "9718",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_star["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_amazon := events_by_id.get(17306):
            conditions.append(
                {
                    "linkedVerseId": 10004,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.PLAY_SONGS_IN_FAVORITE.value,
                            "conditionList": "712;777",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_amazon["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_crystal := events_by_id.get(17409):
            conditions.append(
                {
                    "linkedVerseId": 10005,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.CLEAR_TEAM_COURSE_WITH_CHARACTER_OF_MINIMUM_RANK.value,
                            "conditionList": "26",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_crystal["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_paradise := events_by_id.get(17485):
            conditions.append(
                {
                    "linkedVerseId": 10006,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.PLAY_SONGS.value,
                            "conditionList": "180_384_2355;407_2353;788_629_600;2704;2050_2354",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_paradise["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_new := events_by_id.get(18081):
            conditions.append(
                {
                    "linkedVerseId": 10007,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.AVATAR_ACCESSORY_EQUIPPED.value,
                            "conditionList": "6104401;6204401;6704401",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_new["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_sun := events_by_id.get(18406):
            conditions.append(
                {
                    "linkedVerseId": 10008,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.PLAY_SONGS_IN_ONLINE_BATTLE.value,
                            # I'm so Happy, U&iVERSE, RELOAD, Mutation, Stardust:RAY
                            # Songs that were shared through online battle
                            "conditionList": "2597;2556;2326;2327;2266",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_sun["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_luminous := events_by_id.get(18553):
            conditions.append(
                {
                    "linkedVerseId": 10009,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.MAP_CLEARED.value,
                            "conditionList": "3020815",  # Secret AREA: LUMINOUS
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_luminous["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_verse := events_by_id.get(18683):
            conditions.append(
                {
                    "linkedVerseId": 10010,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.PLAY_SONGS_IN_RECOMMENDED_FOLDER.value,
                            "conditionList": "2802;2705;2712",  # Lock-on Rush, Theatore Creatore, Crossmythos Rhapsodia
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_verse["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_xverse := events_by_id.get(18685):
            # This is probably not the correct condition, but officially gate X-VERSE opens immediately
            # after all 10 gates are cleared, so we can probably use this unlock condition.
            conditions.append(
                {
                    "linkedVerseId": 10011,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": 31,
                            "conditionList": "10001;10002;10003;10004;10005;10006;10007;10008;10009;10010",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_xverse["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_reverse := events_by_id.get(18684):
            # Gate RE:VERSE opens after playing all 10 Linked MUSIC tracks.
            conditions.append(
                {
                    "linkedVerseId": 10012,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": 44,
                            "conditionList": "2968;2969;2970;2971;2972;2973;2974;2975;2976;2977;2978",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": gate_reverse["startDate"].strftime(
                                self.date_time_format
                            ),
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        if gate_universe := events_by_id.get(18686):
            # Gate UNIVERSE opens after gate RE:VERSE is cleared, again notes from gate X-VERSE applies.
            start_date = gate_universe["startDate"].strftime(self.date_time_format)

            conditions.append(
                {
                    "linkedVerseId": 10013,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.SPECIAL_CLEAR.value,
                            "conditionList": "10012",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )
            conditions.append(
                {
                    "linkedVerseId": 10014,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": LinkedVerseUnlockConditionType.SPECIAL_CLEAR.value,
                            "conditionList": "10013",
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        return {
            "length": len(conditions),
            "gameLinkedVerseConditionUnlockList": conditions,
        }
