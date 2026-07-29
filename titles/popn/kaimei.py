from core.eamuse import BaseHandler
from core.config import CoreConfig
from core.eamuse import EAProtocol
from core.eaapi import XMLNode, Type
from datetime import datetime
from typing import List

from .config import PopnConfig
from .const import PopnConstants
from .peace import PopnPeace


class PopnKaimei(PopnPeace):
    def __init__(
        self,
        core_config: CoreConfig,
        game_config: PopnConfig,
        protocol: EAProtocol,
    ) -> None:
        super().__init__(core_config, game_config, protocol)
        self.version = PopnConstants.VER_KAIMEI
