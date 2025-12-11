from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
    MapAreaConditionLogicalOperator,
    MapAreaConditionType,
)

from .xverse import ChuniXVerse


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

        return {
            "length": len(map_area_condition_list),
            "gameMapAreaConditionList": map_area_condition_list,
        }
