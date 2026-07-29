from core.data import Data
from core.config import CoreConfig
#from .schema import *


class PopnData(Data):
    def __init__(self, cfg: CoreConfig) -> None:
        super().__init__(cfg)

        #self.item = PopnItemData(cfg, self.session)
        #self.profile = PopnProfileData(cfg, self.session)
        #self.score = PopnScoreData(cfg, self.session)
        #self.static = PopnStaticData(cfg, self.session)
        #self.lobby = PopnLobbyData(cfg, self.session)
