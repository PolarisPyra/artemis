import struct
from typing import Tuple, List, Dict

from .base import IDZHandlerBase
from artemis.config import ArtemisConfig
from ..config import IDZConfig


class IDZHandlerLoadTopTen(IDZHandlerBase):
    cmd_codes = [0x012C] * 4
    rsp_codes = [0x00CE] * 4
    name = "load_top_ten"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
        self.size = 0x1720

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        tracks_dates: List[Tuple[int, int]] = []
        for i in range(32):
            tracks_dates.append(
                (
                    struct.unpack_from("<H", data, 0x04 + (2 * i))[0],
                    "little",
                    struct.unpack_from("<I", data, 0x44 + (4 * i))[0],
                    "little",
                )
            )
        # TODO: Best scores
        for i in range(3):
            offset = 0x16C0 + 0x1C * i
            struct.pack_into("<B", ret, offset + 0x02, 0xFF)

        return ret
