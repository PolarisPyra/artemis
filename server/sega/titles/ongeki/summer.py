from typing import Dict, Any

from server.sega.config import ArtemisConfig
from server.sega.titles.ongeki.base import OngekiBase
from server.sega.titles.ongeki.const import OngekiConstants
from server.sega.titles.ongeki.config import OngekiConfig


class OngekiSummer(OngekiBase):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: OngekiConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = OngekiConstants.VER_ONGEKI_SUMMER

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.10.00"
        ret["gameSetting"]["onlineDataVersion"] = "1.10.00"
        return ret
