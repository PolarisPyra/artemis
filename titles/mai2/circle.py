import datetime
from typing import Dict

from core.config import CoreConfig

from .config import Mai2Config
from .const import Mai2Constants
from .prismplus import Mai2PrismPlus


class Mai2Circle(Mai2PrismPlus):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_CIRCLE

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker
        user_data["lastDataVersion"] = "1.60.00"
        return user_data

    async def handle_get_game_festa_api_request(self, data: Dict) -> Dict:
        place_id: int = data["placeId"]

        return {
            "gameFestaData": {
                "eventId": 0,
                "isRallyPeriod": False,
                "isCircleJoinNotAllowed": False,
                "jackingFestaSideId": 0,
                "festaSideDataList": [],  # festaSideId: int, rankInPlace: int, advantagePercent: int
            },
            "gameResultFestaData": {
                "eventId": 0,
                "resultFestaSideDataList": [],  # festaSideId: int, rank: int, advantagePercent: int
            },
        }

    async def handle_get_place_circle_data_api_request(self, data: Dict) -> Dict:
        place_id: int = data["placeId"]

        return {
            "returnCode": 0,  # returnCode has to be != 0 if a place circle exists
            "circleId": 0,
            "aggrDate": (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=9)
            ).strftime(self.date_time_format),
        }

    async def handle_get_user_circle_data_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]

        return {
            "circleId": 0,
            "circleName": "",
            "isPlace": False,
            "circleClass": 0,
            "lastLoginDate": "1970-01-01 00:00:00",
            "circlePointRankingList": [],  # userId: int, userName: str, rank: int, point: int
        }

    async def handle_get_user_circle_point_data_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        circle_id: int = data["circleId"]

        return {
            "userId": user_id,
            "aggrDate": (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=9)
            ).strftime(self.date_time_format),
            "userCirclePointDataList": [],  # circleId: int, userName: str, aggrDate: str, point: int, recordDate: str, rewardGet: bool
        }

    async def handle_get_user_circle_point_ranking_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        circle_id: int = data["circleId"]

        return {
            "circleId": 0,
            "circleName": "",
            "aggrDate": (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=9)
            ).strftime(self.date_time_format),
            "lastMonthCircleRank": 0,
            "lastMonthPoint": 0,
        }

    async def handle_get_user_festa_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]

        return {
            "userFestaData": {
                "eventId": 0,
                "circleId": 0,
                "festaSideId": 0,
                "circleTotalFestaPoint": 0,
                "currentTotalFestaPoint": 0,
                "circleRankInFestaSide": 0,
                "circleRecordDate": (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(hours=9)
                ).strftime(self.date_time_format),
                "isDailyBonus": False,
                "participationRewardGet": False,
                "receivedRewardBorder": 0,
            },
            "userResultFestaData": {
                "eventId": 0,
                "circleId": 0,
                "circleName": "",
                "festaSideId": 0,
                "circleRankInFestaSide": 0,
                "receivedRewardBorder": 0,
                "circleTotalFestaPoint": 0,
                "resultRewardGet": False,
            },
        }

    async def handle_upsert_user_place_circle_regist_api_request(self, data: Dict) -> Dict:
        user_id: int = data["userId"]
        circle_id: int = data["circleId"]

        return {"returnCode": 0, "apiName": "UpsertUserPlaceCircleRegistApi"}
