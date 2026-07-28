from server.sega.data import Data
from server.sega.config import ArtemisConfig
from server.sega.titles.diva.schema import (
    DivaProfileData,
    DivaScoreData,
    DivaModuleData,
    DivaCustomizeItemData,
    DivaPvCustomizeData,
    DivaItemData,
    DivaStaticData,
)


class DivaData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = DivaProfileData(self.config, self.session)
        self.score = DivaScoreData(self.config, self.session)
        self.module = DivaModuleData(self.config, self.session)
        self.customize = DivaCustomizeItemData(self.config, self.session)
        self.pv_customize = DivaPvCustomizeData(self.config, self.session)
        self.item = DivaItemData(self.config, self.session)
        self.static = DivaStaticData(self.config, self.session)
