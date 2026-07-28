from server.sega.data import Data
from server.sega.config import ArtemisConfig


class CardMakerData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)
        # empty Card Maker database
