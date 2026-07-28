from artemis.config import ArtemisConfig
from artemis.data import Data
from titles.ongeki.schema import (
    CozynetStaticOngekiData,
    OngekiItemData,
    OngekiLogData,
    OngekiProfileData,
    OngekiScoreData,
    OngekiStaticData,
)


class OngekiData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.cozynet = CozynetStaticOngekiData(cfg, self.session)
        self.item = OngekiItemData(cfg, self.session)
        self.profile = OngekiProfileData(cfg, self.session)
        self.score = OngekiScoreData(cfg, self.session)
        self.static = OngekiStaticData(cfg, self.session)
        self.log = OngekiLogData(cfg, self.session)
