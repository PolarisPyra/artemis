from typing import Dict

from artemis.config import ArtemisConfig
from titles.chuni.base import ChuniBase
from titles.chuni.const import ChuniConstants
from titles.chuni.config import ChuniConfig


class ChuniStar(ChuniBase):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_STAR

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.20.00"
        return ret
