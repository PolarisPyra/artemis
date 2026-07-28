import struct
from typing import Tuple, List, Dict

from .base import IDZHandlerBase
from server.sega.config import ArtemisConfig
from ..config import IDZConfig


class IDZHandlerDiscoverProfile(IDZHandlerBase):
    cmd_codes = [0x006B, 0x0067]
    rsp_codes = [0x006C, 0x0068, 0x0068, 0x0068]
    name = "discover_profile"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
        self.size = 0x0010

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        user_id = struct.unpack_from("<I", data, 0x04)[0]
        profile = None

        struct.pack_into("<H", ret, 0x04, int(profile is not None))
        return ret
