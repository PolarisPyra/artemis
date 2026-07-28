import struct

from .base import IDZHandlerBase
from artemis.config import ArtemisConfig
from ..config import IDZConfig
from ..const import IDZConstants


class IDZHandlerSaveTimeAttack(IDZHandlerBase):
    cmd_codes = [0x00CD, 0x0136, 0x0136, 0x0136]
    rsp_codes = [0x00CE, 0x00CE, 0x00CD, 0x00CD]
    name = "save_time_attack"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
        self.size = 0x00B0

        if self.version > IDZConstants.VER_IDZ_130:
            self.size = 0x00F0

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
