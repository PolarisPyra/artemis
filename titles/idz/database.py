from artemis.data import Data
from artemis.config import ArtemisConfig


class IDZData(Data):
    def __init__(self, cfg: ArtemisConfig) -> None:
        super().__init__(cfg)
