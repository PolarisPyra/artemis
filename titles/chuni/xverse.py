import itertools
from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import (
    ChuniConstants,
    MapAreaConditionLogicalOperator,
    MapAreaConditionType,
)

from .verse import ChuniVerse


class ChuniXVerse(ChuniVerse):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_X_VERSE

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.35.00"
        return user_data

    async def handle_cm_get_user_data_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_data(data["userId"], self.version)

        if p is None:
            return {}

        profile = p._asdict()
        profile.pop("id")
        profile.pop("user")
        profile.pop("version")

        return {
            "userId": data["userId"],
            "userData": profile,
            "userEmoney": [
                {
                    "type": 0,
                    "emoneyCredit": 100,
                    "emoneyBrand": 1,
                    "ext1": 0,
                    "ext2": 0,
                    "ext3": 0,
                }
            ],
        }

    async def handle_get_user_data_api_request(self, data: Dict) -> Dict:
        p = await self.data.profile.get_profile_data(data["userId"], self.version)

        if p is None:
            return {}

        profile = p._asdict()
        profile.pop("id")
        profile.pop("user")
        profile.pop("version")

        return {"userId": data["userId"], "userData": profile}

    async def handle_get_user_c_mission_list_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        rows = await self.data.item.get_cmissions_and_progress(user_id) or []
        user_mission_list = []

        for mission_id, progress_rows in itertools.groupby(
            rows, key=lambda r: r.missionId
        ):
            mission = {
                "userId": user_id,
                "missionId": mission_id,
                "point": 0,
                "userCMissionProgressList": [],
            }

            for row in progress_rows:
                mission["point"] = row.point
                mission["userCMissionProgressList"].append(
                    {
                        "order": row.order,
                        "stage": row.stage,
                        "progress": row.progress,
                    }
                )

            user_mission_list.append(mission)

        return {
            "userId": user_id,
            "userCMissionList": user_mission_list,
        }

    async def handle_get_game_lv_condition_open_api_request(self, data: Dict) -> Dict:
        return {
            "length": 1,
            "gameLinkedVerseConditionOpenList": [
                {
                    "linkedVerseId": 10001,
                    "length": 1,
                    "conditionList": [
                        {
                            "type": MapAreaConditionType.MAP_CLEARED.value,
                            "conditionId": 3020803,
                            "logicalOpe": MapAreaConditionLogicalOperator.AND.value,
                            "startDate": "2025-07-16 10:00:00",
                            "endDate": "2099-12-31 23:59:59",
                        }
                    ],
                }
            ],
        }

    async def handle_get_game_lv_condition_unlock_api_request(self, data: Dict) -> Dict:
        return {
            "length": 0,
            "gameLinkedVerseConditionUnlockList": [],
        }

    async def handle_get_user_lv_api_request(self, data: Dict) -> Dict:
        user_id = int(data["userId"])
        rows = await self.data.profile.get_linked_verse(user_id) or []
        linked_verses = []

        for row in rows:
            data = row._asdict()
            data.pop("id")
            data.pop("user")

            linked_verses.append(data)

        return {
            "userId": user_id,
            "userLinkedVerseList": linked_verses,
        }

    async def handle_begin_raid_matching_api_request(self, data: Dict) -> Dict:
        return await super().handle_begin_matching_api_request(data)

    async def handle_end_raid_matching_api_request(self, data: Dict) -> Dict:
        return await super().handle_end_matching_api_request(data)

    async def handle_get_raid_matching_state_api_request(self, data: Dict) -> Dict:
        return await super().handle_get_matching_state_api_request(data)
