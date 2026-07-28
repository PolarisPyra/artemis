from typing import Any, List, Dict
from datetime import datetime, timedelta
import pytz
import json

from server.sega.config import ArtemisConfig
from server.sega.titles.mai2.splash import Mai2Splash
from server.sega.titles.mai2.config import Mai2Config
from server.sega.titles.mai2.const import Mai2Constants


class Mai2SplashPlus(Mai2Splash):
    def __init__(self, cfg: ArtemisConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_DX_SPLASH_PLUS
