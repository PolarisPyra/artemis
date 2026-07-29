from core.config import CoreConfig
from core.eamuse import EAProtocol

from .config import PopnConfig
from .const import PopnConstants
from .unilab import PopnUnilab


class PopnJamFizz(PopnUnilab):
    """pop'n music Jam&Fizz, inheriting the UniLab protocol layout."""

    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_JAM_FIZZ
