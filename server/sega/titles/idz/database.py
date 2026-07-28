from server.sega.data import Data
from server.sega.config import ArtemisConfig


class IDZData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)
