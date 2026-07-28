import struct

from .base import IDZHandlerBase
from artemis.config import ArtemisConfig
from ..config import IDZConfig
from ..const import IDZConstants


class IDZHandlerUpdateStoryClearNum(IDZHandlerBase):
    cmd_codes = [0x007F, 0x097F, 0x013D, 0x0144]
    rsp_codes = [0x0080, 0x013E, 0x013E, 0x0145]
    name = "update_story_clear_num"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)

        if self.version == IDZConstants.VER_IDZ_110:
            self.size = 0x0220
        elif self.version == IDZConstants.VER_IDZ_130:
            self.size = 0x04F0
        elif self.version == IDZConstants.VER_IDZ_210:
            self.size = 0x0510
        elif self.version == IDZConstants.VER_IDZ_230:
            self.size = 0x0800

    def handle(self, data: bytes) -> bytearray:
        return super().handle(data)
