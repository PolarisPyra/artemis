import struct

from .base import IDZHandlerBase
from artemis.config import ArtemisConfig
from ..config import IDZConfig
from ..const import IDZConstants


class IDZHandleUpdateUserLog(IDZHandlerBase):
    cmd_codes = [0x00BD, 0x00BD, 0x00AB, 0x00B3]
    name = "update_user_log"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)

    def handle(self, data: bytes) -> bytearray:
        ret = super().handle(data)
        return ret
