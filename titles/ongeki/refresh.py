from typing import Any, Dict

from artemis.config import ArtemisConfig
from titles.ongeki.const import OngekiConstants

from .brightmemory import OngekiBrightMemory
from .config import OngekiConfig


class OngekiReFresh(OngekiBrightMemory):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: OngekiConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = OngekiConstants.VER_ONGEKI_REFRESH

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.50.00"
        ret["gameSetting"]["onlineDataVersion"] = "1.50.00"

        return ret
    
    async def handle_get_user_preview_api_request(self, data: Dict) -> Dict:
        profile = await self.data.profile.get_profile_preview(
            data["userId"], self.version
        )

        if profile is None:
            return {
                "userId": data["userId"],
                "isLogin": False,
                "lastLoginDate": "0000-00-00 00:00:00",
                "userName": "",
                "reincarnationNum": 0,
                "level": 0,
                "exp": 0,
                "playerRating": 0,
                "newPlayerRating": 0,
                "lastGameId": "",
                "lastRomVersion": "",
                "lastDataVersion": "",
                "lastPlayDate": "",
                "nameplateId": 0,
                "trophyId": 0,
                "cardId": 0,
                "dispPlayerLv": 0,
                "dispRating": 0,
                "dispBP": 0,
                "headphone": 0,
                "banStatus": 0,
                "isWarningConfirmed": True,
                "lastEmoneyBrand": 0,
                "lastEmoneyCredit": 0,
            }

        return {
            "userId": data["userId"],
            "isLogin": False,
            "lastLoginDate": profile["lastPlayDate"],
            "userName": profile["userName"],
            "reincarnationNum": profile["reincarnationNum"],
            "level": profile["level"],
            "exp": profile["exp"],
            "playerRating": profile["playerRating"],
            "newPlayerRating": profile["newPlayerRating"],
            "lastGameId": profile["lastGameId"],
            "lastRomVersion": profile["lastRomVersion"],
            "lastDataVersion": profile["lastDataVersion"],
            "lastPlayDate": profile["lastPlayDate"],
            "nameplateId": profile["nameplateId"],
            "trophyId": profile["trophyId"],
            "cardId": profile["cardId"],
            "dispPlayerLv": profile["dispPlayerLv"],
            "dispRating": profile["dispRating"],
            "dispBP": profile["dispBP"],
            "headphone": profile["headphone"],
            "banStatus": profile["banStatus"],
            "isWarningConfirmed": True,
            "lastEmoneyBrand": 0,
            "lastEmoneyCredit": 0,
        }

    async def handle_get_user_skin_api_request(self, data: Dict) -> Dict:
        user_id = data["userId"]
        skin_rows = await self.data.item.get_skins(user_id)
        skin_list = []

        for row in (skin_rows or []):
            data = row._asdict()
            data.pop("id")
            data.pop("user")

            skin_list.append(data)

        return {
            "userId": user_id,
            "length": len(skin_list),
            "userSkinList": skin_list,
        }

    async def handle_get_user_event_map_api_request(self, data: Dict[str, int]) -> Dict[str, Any]:
        user_id = data["userId"]
        event_id = data["eventId"]
        map_id = data["mapId"]
        event_map_row = await self.data.item.get_event_map(user_id, event_id, map_id)

        if event_map_row is None:
            return {
                "userId": user_id,
                "userEventMap": {},
            }

        event_map = event_map_row._asdict()
        event_map.pop("id")
        event_map.pop("user")
        
        return {
            "userId": user_id,
            "userEventMap": event_map,
        }

