from server.sega.data import Data
from server.sega.config import ArtemisConfig

from .schema import *


class SaoData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.item = SaoItemData(cfg, self.session)
        self.profile = SaoProfileData(cfg, self.session)
        self.static = SaoStaticData(cfg, self.session)
