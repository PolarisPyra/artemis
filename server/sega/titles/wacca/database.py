from server.sega.data import Data
from server.sega.config import ArtemisConfig
from server.sega.titles.wacca.schema import *


class WaccaData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = WaccaProfileData(self.config, self.session)
        self.score = WaccaScoreData(self.config, self.session)
        self.item = WaccaItemData(self.config, self.session)
        self.static = WaccaStaticData(self.config, self.session)
