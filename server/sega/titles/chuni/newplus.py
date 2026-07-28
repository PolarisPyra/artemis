from typing import Dict, Any

from server.sega.utils import Utils
from server.sega.config import ArtemisConfig
from server.sega.titles.chuni.new import ChuniNew
from server.sega.titles.chuni.const import ChuniConstants
from server.sega.titles.chuni.config import ChuniConfig


class ChuniNewPlus(ChuniNew):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_NEW_PLUS

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # hardcode lastDataVersion for CardMaker 1.35 A028
        user_data["lastDataVersion"] = "2.05.00"
        return user_data
