import struct

from .base import IDZHandlerBase
from server.sega.config import ArtemisConfig
from ..config import IDZConfig


class IDZHandlerSaveTopic(IDZHandlerBase):
    cmd_codes = [0x009A, 0x009A, 0x0091, 0x0091]
    rsp_codes = [0x009B, 0x009B, 0x0092, 0x0092]
    name = "save_topic"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
        self.size = 0x05D0

    def handle(self, data: bytes) -> bytearray:
        return super().handle(data)
