import logging

from server.sega.config import ArtemisConfig
from server.sega.titles.idac.config import IDACConfig
from server.sega.titles.idac.const import IDACConstants
from server.sega.titles.idac.database import IDACData


class IDACBase:
    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDACConfig) -> None:
        self.artemis_cfg = artemis_cfg
        self.game_config = game_cfg
        self.game = IDACConstants.GAME_CODE
        self.version = IDACConstants.VER_IDAC_SEASON_1
        self.data = IDACData(artemis_cfg)
        self.logger = logging.getLogger("idac")
