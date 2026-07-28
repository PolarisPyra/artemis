from typing import Dict

from server.sega.config import ArtemisConfig
from server.sega.data.cache import cached
from server.sega.titles.cm.base import CardMakerBase
from server.sega.titles.cm.const import CardMakerConstants
from server.sega.titles.cm.config import CardMakerConfig


class CardMaker135(CardMakerBase):
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: CardMakerConfig) -> None:
        super().__init__(artemis_cfg, game_cfg)
        self.version = CardMakerConstants.VER_CARD_MAKER_135

    async def handle_get_game_setting_api_request(self, data: Dict) -> Dict:
        ret = await super().handle_get_game_setting_api_request(data)
        ret["gameSetting"]["dataVersion"] = "1.35.00"
        return ret
