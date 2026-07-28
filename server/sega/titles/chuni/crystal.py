from datetime import datetime, timedelta
from typing import Dict, Any
import pytz

from server.sega.config import ArtemisConfig
from server.sega.titles.chuni.base import ChuniBase
from server.sega.titles.chuni.const import ChuniConstants
from server.sega.titles.chuni.config import ChuniConfig


class ChuniCrystal(ChuniBase):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_CRYSTAL

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.40.00"
        return ret
