from core.data import Data
from core.config import CoreConfig
from titles.chuni.schema import (
    ChuniItemData,
    ChuniProfileData,
    ChuniScoreData,
    ChuniStaticData,
    CozynetStaticData,
)
from titles.chuni.schema.client import ChuniClientData


class ChuniData(Data):
    def __init__(self, cfg: CoreConfig) -> None:
        super().__init__(cfg)

        self.item = ChuniItemData(cfg, self.session)
        self.profile = ChuniProfileData(cfg, self.session)
        self.score = ChuniScoreData(cfg, self.session)
        self.static = ChuniStaticData(cfg, self.session)
        self.cozynet = CozynetStaticData(cfg, self.session)
        self.client = ChuniClientData(cfg, self.session)
