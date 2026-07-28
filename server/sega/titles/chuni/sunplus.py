from typing import Dict, Any

from server.sega.config import ArtemisConfig
from server.sega.titles.chuni.sun import ChuniSun
from server.sega.titles.chuni.const import ChuniConstants
from server.sega.titles.chuni.config import ChuniConfig


class ChuniSunPlus(ChuniSun):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_SUN_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # I don't know if lastDataVersion is going to matter, I don't think CardMaker 1.35 works this far up
        user_data["lastDataVersion"] = "2.15.00"
        return user_data
