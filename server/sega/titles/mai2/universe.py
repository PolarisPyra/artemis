from typing import Any, List, Dict
from random import randint
from datetime import datetime, timedelta

from server.sega.config import ArtemisConfig
from server.sega.titles.mai2.splashplus import Mai2SplashPlus
from server.sega.titles.mai2.const import Mai2Constants
from server.sega.titles.mai2.config import Mai2Config


class Mai2Universe(Mai2SplashPlus):
    def __init__(self, cfg: ArtemisConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_UNIVERSE
