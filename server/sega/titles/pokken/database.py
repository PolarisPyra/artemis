from server.sega.data import Data
from server.sega.config import ArtemisConfig

from .schema import *


class PokkenData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = PokkenProfileData(cfg, self.session)
        self.match = PokkenMatchData(cfg, self.session)
        self.item = PokkenItemData(cfg, self.session)
        self.static = PokkenStaticData(cfg, self.session)
