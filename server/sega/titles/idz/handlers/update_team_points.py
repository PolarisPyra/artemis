import struct

from .base import IDZHandlerBase
from server.sega.config import ArtemisConfig
from ..config import IDZConfig
from ..const import IDZConstants


class IDZHandleUpdateTeamPoints(IDZHandlerBase):
    cmd_codes = [0x0081, 0x0081, 0x007B, 0x007B]
    name = "unlock_profile"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
