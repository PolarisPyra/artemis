from core.config import CoreConfig
from core.data import Data
from titles.popn.schema import PopnProfileData, PopnScoreData


class PopnData(Data):
    def __init__(self, cfg: CoreConfig) -> None:
        super().__init__(cfg)
        self.profile = PopnProfileData(cfg, self.session)
        self.score = PopnScoreData(cfg, self.session)
