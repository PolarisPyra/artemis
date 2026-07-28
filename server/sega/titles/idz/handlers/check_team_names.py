import struct

from .base import IDZHandlerBase
from server.sega.config import ArtemisConfig
from ..config import IDZConfig


class IDZHandlerCheckTeamName(IDZHandlerBase):
    cmd_codes = [0x00A2, 0x00A2, 0x0097, 0x0097]
    rsp_codes = [0x00A3, 0x00A3, 0x0098, 0x0098]
    name = "check_team_name"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
        self.size = 0x0010

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        struct.pack_into("<I", ret, 0x4, 0x1)
        return data
