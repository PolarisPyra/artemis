from server.sega.data import Data
from server.sega.config import ArtemisConfig
from server.sega.titles.mai2.schema import (
    Mai2ItemData,
    Mai2ProfileData,
    Mai2StaticData,
    Mai2ScoreData,
)


class Mai2Data(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = Mai2ProfileData(self.config, self.session)
        self.item = Mai2ItemData(self.config, self.session)
        self.static = Mai2StaticData(self.config, self.session)
        self.score = Mai2ScoreData(self.config, self.session)
