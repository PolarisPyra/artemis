import struct

from .base import IDZHandlerBase
from server.sega.config import ArtemisConfig
from ..config import IDZConfig
from ..const import IDZConstants


class IDZHandleUpdateUIReport(IDZHandlerBase):
    cmd_codes = [0x0084, 0x0084, 0x007E, 0x007E]
    name = "update_ui_report"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
