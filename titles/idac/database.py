from artemis.data import Data
from artemis.config import ArtemisConfig
from titles.idac.schema.profile import IDACProfileData
from titles.idac.schema.item import IDACItemData


class IDACData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)

        self.profile = IDACProfileData(cfg, self.session)
        self.item = IDACItemData(cfg, self.session)
