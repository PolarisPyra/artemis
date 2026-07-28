from typing import Any, List, Dict
from datetime import datetime, timedelta
import json

from server.sega.config import ArtemisConfig
from server.sega.titles.wacca.base import WaccaBase
from server.sega.titles.wacca.config import WaccaConfig
from server.sega.titles.wacca.const import WaccaConstants

from server.sega.titles.wacca.handlers import *


class WaccaS(WaccaBase):
    def __init__(self, cfg: ArtemisConfig, game_cfg: WaccaConfig) -> None:
        super().__init__(cfg, game_cfg)
        self.version = WaccaConstants.VER_WACCA_S
        self.allowed_stages = [
            (1513, 13),
            (1512, 12),
            (1511, 11),
            (1510, 10),
            (1509, 9),
            (1508, 8),
            (1507, 7),
            (1506, 6),
            (1505, 5),
            (1504, 4),
            (1503, 3),
            (1502, 2),
            (1501, 1),
        ]

    async def handle_advertise_GetNews_request(self, data: Dict) -> Dict:
        resp = GetNewsResponseV2()
        return resp.make()
