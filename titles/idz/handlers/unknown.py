import struct

from .base import IDZHandlerBase
from artemis.config import ArtemisConfig
from ..config import IDZConfig


class IDZHandlerUnknown(IDZHandlerBase):
    cmd_codes = [0x00AD, 0x00AD, 0x00A2, 0x00A2]
    name = "unknown"

    def __init__(self, artemis_cfg: ArtemisConfig, game_cfg: IDZConfig, version: int) -> None:
        super().__init__(artemis_cfg, game_cfg, version)
