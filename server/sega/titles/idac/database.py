from server.sega.data import Data
from server.sega.config import ArtemisConfig
from server.sega.titles.idac.schema.profile import IDACProfileData
from server.sega.titles.idac.schema.item import IDACItemData


class IDACData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = IDACProfileData(cfg, self.session)
        self.item = IDACItemData(cfg, self.session)
