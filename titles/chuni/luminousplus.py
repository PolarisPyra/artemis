from datetime import timedelta
from typing import Dict

from artemis.config import ArtemisConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
    MapAreaConditionLogicalOperator,
    MapAreaConditionType,
)
from titles.chuni.luminous import ChuniLuminous


class ChuniLuminousPlus(ChuniLuminous):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.25.00"
        return user_data

    async def handle_get_user_c_mission_list_api_request(self, data: Dict) -> Dict:
        # Works on my machine
        user_id = data["userId"]
        user_mission_list_req = data["userCMissionList"]

        user_mission_list = []
        for mission in user_mission_list_req:
            user_id = mission["userId"]
            mission_id = mission["missionId"]
            point = mission["point"]

            mission_data = await self.data.item.get_cmission(user_id, mission_id)
            progress_data = await self.data.item.get_cmission_progress(
                user_id, mission_id
            )

            user_mission_progress_list = []
            if mission_data and progress_data:
                point = mission_data["point"]
                user_mission_progress_list = [
                    {
                        "order": progress["order"],
                        "stage": progress["stage"],
                        "progress": progress["progress"],
                    }
                    for progress in progress_data
                ]

            user_mission_list.append(
                {
                    "userId": user_id,
                    "missionId": mission_id,
                    "point": point,
                    "userCMissionProgressList": user_mission_progress_list,
                }
            )

        return {
            "userId": user_id,
            "userCMissionList": user_mission_list,
        }

    async def handle_get_game_map_area_condition_api_request(self, data: Dict) -> Dict:
        # There is no game data for this, everything is server side.
        # However, we can selectively show/hide events as data is imported into the server.
        map_area_condition_list = []
        events = await self.data.static.get_enabled_events(self.version)

        if events is None:
            return {
                "length": len(map_area_condition_list),
                "gameMapAreaConditionList": map_area_condition_list,
            }

        event_by_id = {evt["eventId"]: evt for evt in events}

        # The Mystic Rainbow of LUMINOUS PLUS map unlocks when any mainline
        # LUMINOUS PLUS areas are completed
        mystic_area_1_conditions = {
            "mapAreaId": 3229601,
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
            nonlocal event_by_id

            if (event := event_by_id.get(map_flag_event_id)) is None:
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

        # Mystic Rainbow of LUMINOUS PLUS Area 2 unlocks when LUMINOUS ep. IV is finished.
        add_mystic_area_condition(15005, 3020704, 3229602)

        # Mystic Rainbow of LUMINOUS PLUS Area 3 unlocks when LUMINOUS ep. V is finished.
        add_mystic_area_condition(15306, 3020705, 3229603)

        # Mystic Rainbow of LUMINOUS PLUS Area 4 unlocks when LUMINOUS ep. VI is finished.
        add_mystic_area_condition(15451, 3020706, 3229604)

        # Mystic Rainbow of LUMINOUS PLUS Area 5 unlocks when LUMINOUS ep. VII is finished.
        add_mystic_area_condition(15506, 3020707, 3229605)

        # 1UM1N0U5 ep. 111 continues. The map is automatically unlocked after finishing
        # LUMINOUS ep. III in LUMINOUS PLUS.
        if ep_111 := event_by_id.get(15009):
            start_date = ep_111["startDate"].strftime(self.date_time_format)

            map_area_condition_list.append(
                {
                    "mapAreaId": 3229207,
                    "length": 1,
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020703,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        },
                    ],
                }
            )

        # ■・■■■■■■・■
        # Finish LUMINOUS ep. IV and obtain the title 「ここは…何処なんだ…？」.
        if re_fiction_o := event_by_id.get(15032):
            start_date = re_fiction_o["startDate"].strftime(self.date_time_format)

            map_area_condition_list.append(
                {
                    "mapAreaId": 3229501,
                    "length": 2,
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020704,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        },
                        {
                            "type": MapAreaConditionType.TROPHY_OBTAINED.value,
                            "conditionId": 7105,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        },
                    ],
                }
            )

        # The Conductor's Path
        # ALL JUSTICE CRITICAL 其のエメラルドを見よ MASTER.
        if the_conductors_path := event_by_id.get(15033):
            start_date = the_conductors_path["startDate"].strftime(
                self.date_time_format
            )

            map_area_condition_list.append(
                {
                    "mapAreaId": 3229701,
                    "length": 1,
                    "mapAreaConditionList": [
                        {
                            "type": MapAreaConditionType.ALL_JUSTICE_CRITICAL.value,
                            "conditionId": 260003,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start_date,
                            "endDate": "2099-12-31 00:00:00",
                        }
                    ],
                }
            )

        # LUMINOUS ep. Ascension
        if ep_ascension := event_by_id.get(15512):
            start_date = ep_ascension["startDate"].replace(hour=0, minute=0, second=0)

            # Finish LUMINOUS ep. VII to unlock LUMINOUS ep. Ascension.
            task_track_map_conditions = [
                {
                    "type": MapAreaConditionType.MAP_CLEARED.value,
                    "conditionId": 3020707,
                    "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                    "startDate": start_date.strftime(self.date_time_format),
                    "endDate": "2099-12-31 00:00:00",
                }
            ]

            # You also need to reach a specific rank on Acid God MASTER.
            # This condition lowers every 7 days.
            # After the first 4 weeks, you only need to finish ep. VII.
            for i, typ in enumerate(
                [
                    MapAreaConditionType.RANK_SSSP.value,
                    MapAreaConditionType.RANK_SSS.value,
                    MapAreaConditionType.RANK_SS.value,
                    MapAreaConditionType.RANK_S.value,
                ]
            ):
                start = start_date + timedelta(days=7 * i)
                end = start_date + timedelta(days=7 * (i + 1)) - timedelta(seconds=1)

                task_track_map_conditions.append(
                    {
                        "type": typ,
                        "conditionId": 265103,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": start.strftime(self.date_time_format),
                        "endDate": end.strftime(self.date_time_format),
                    }
                )

            map_area_condition_list.extend(
                [
                    {
                        "mapAreaId": map_area_id,
                        "length": len(task_track_map_conditions),
                        "mapAreaConditionList": task_track_map_conditions,
                    }
                    for map_area_id in {3220801, 3220802, 3220803, 3220804}
                ]
            )

            # To unlock the final map area (Forsaken Tale), achieve a specific rank
            # on the 4 task tracks in the previous map areas. This condition also lowers
            # every 7 days, similar to Acid God.
            # After 28 days, you only need to finish the other 4 areas in ep. Ascension.
            forsaken_tale_conditions = []

            for i, typ in enumerate(
                [
                    MapAreaConditionType.RANK_SSSP.value,
                    MapAreaConditionType.RANK_SSS.value,
                    MapAreaConditionType.RANK_SS.value,
                    MapAreaConditionType.RANK_S.value,
                ]
            ):
                start = start_date + timedelta(days=7 * i)
                end = start_date + timedelta(days=7 * (i + 1)) - timedelta(seconds=1)

                forsaken_tale_conditions.extend(
                    [
                        {
                            "type": typ,
                            "conditionId": condition_id,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": start.strftime(self.date_time_format),
                            "endDate": end.strftime(self.date_time_format),
                        }
                        for condition_id in {98203, 108603, 247503, 233903}
                    ]
                )

            forsaken_tale_conditions.extend(
                [
                    {
                        "type": MapAreaConditionType.MAP_AREA_CLEARED.value,
                        "conditionId": map_area_id,
                        "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                        "startDate": (start_date + timedelta(days=28)).strftime(
                            self.date_time_format
                        ),
                        "endDate": "2099-12-31 00:00:00",
                    }
                    for map_area_id in {3220801, 3220802, 3220803, 3220804}
                ]
            )

            map_area_condition_list.append(
                {
                    "mapAreaId": 3220805,
                    "length": len(forsaken_tale_conditions),
                    "mapAreaConditionList": forsaken_tale_conditions,
                }
            )

        # CAVE of RVESE / Episode. _ _ X _ _
        if episode_x := event_by_id.get(15254):
            start_date = (
                episode_x["startDate"]
                .replace(hour=0, minute=0, second=0)
                .strftime(self.date_time_format)
            )

            map_area_condition_list.extend(
                [
                    # Unlock Episode. _ _ X _ _ by finishing HARDCORE TANO*C 4.
                    {
                        "mapAreaId": 2208801,
                        "length": 1,
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.MAP_CLEARED.value,
                                "conditionId": 2006533,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00",
                            },
                        ],
                    },
                    # Equip the trophy 第壱の石版【V】 to unlock Laur's map area
                    {
                        "mapAreaId": 2208802,
                        "length": 1,
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_EQUIPPED.value,
                                "conditionId": 7107,  # 第壱の石板【V】
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00",
                            },
                        ],
                    },
                    # Equip the trophy 第弐の石板【Λ】 to unlock Kanon Oguni's map area
                    {
                        "mapAreaId": 2208803,
                        "length": 1,
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.TROPHY_EQUIPPED.value,
                                "conditionId": 7104,  # 第弐の石板【Λ】
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00",
                            },
                        ],
                    },
                    # Finish map areas 1-3 to access Latent Kingdom.
                    {
                        "mapAreaId": 2208804,
                        "length": 2,
                        "mapAreaConditionList": [
                            {
                                "type": MapAreaConditionType.MAP_AREA_CLEARED.value,
                                "conditionId": map_area_id,
                                "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                                "startDate": start_date,
                                "endDate": "2099-12-31 00:00:00",
                            }
                            for map_area_id in {2208801, 2208802, 2208803}
                        ],
                    },
                ],
            )

        return {
            "length": len(map_area_condition_list),
            "gameMapAreaConditionList": map_area_condition_list,
        }
