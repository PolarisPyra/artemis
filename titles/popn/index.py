from core.config import CoreConfig
from core.eamuse import EAProtocol
import yaml
from os import path
from typing import Tuple
import logging
import coloredlogs
from logging.handlers import TimedRotatingFileHandler

from core.eamuse import BaseDispatcher
from .unilab import PopnUnilab
from .jamfizz import PopnJamFizz
from .hicheers import PopnHiCheers
from .kaimei import PopnKaimei
from .peace import PopnPeace
from .usaneko import PopnUsaneko
from .config import PopnConfig
from .const import PopnConstants


class PopnDispatch(BaseDispatcher):
    def __init__(self, core_config: CoreConfig, config_dir: str) -> None:
        self.core_cfg = core_config
        self.game_cfg = PopnConfig()
        if path.exists(f"{config_dir}/{PopnConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{config_dir}/{PopnConstants.CONFIG_NAME}"))
            )
        self.handlers = {
            PopnConstants.VER_USANEKO: PopnUsaneko,
            PopnConstants.VER_PEACE: PopnPeace,
            PopnConstants.VER_KAIMEI: PopnKaimei,
            PopnConstants.VER_UNILAB: PopnUnilab,
            PopnConstants.VER_JAM_FIZZ: PopnJamFizz,
            PopnConstants.VER_HI_CHEERS: PopnHiCheers,
        }

        self.logger = logging.getLogger("popn")
        if not hasattr(self.logger, "initted"):
            log_fmt_str = "[%(asctime)s] Pop'n Music | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)
            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.core_cfg.server.log_dir, "popn"),
                encoding="utf8",
                when="d",
                backupCount=10,
            )

            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel(self.game_cfg.server.loglevel)
            coloredlogs.install(
                level=self.game_cfg.server.loglevel, logger=self.logger, fmt=log_fmt_str
            )
            self.logger.initted = True

    @classmethod
    def is_game_enabled(
        cls, game_code: str, core_cfg: CoreConfig, config_dir: str
    ) -> Tuple[bool, str, str]:
        game_cfg = PopnConfig()

        if path.exists(f"{config_dir}/{PopnConstants.CONFIG_NAME}"):
            game_cfg.update(
                yaml.safe_load(open(f"{config_dir}/{PopnConstants.CONFIG_NAME}"))
            )

        return (game_cfg.server.enable, "", "")

    async def dispatch(self, protocol: EAProtocol, internal_ver: int):
        handler_cls = self.handlers.get(internal_ver)
        if handler_cls is None:
            self.logger.error(
                "Pop'n version %s has no implemented handler", internal_ver
            )
            return None

        handler = handler_cls(self.core_cfg, self.game_cfg, protocol)
        func_to_find = f"handle_{protocol.method.replace('.', '_')}"
        handler_method = getattr(handler, func_to_find, None)
        if handler_method is None:
            self.logger.warning(
                "%s does not dispatch %s", protocol.model.gamecode, protocol.method
            )
            return None
        return await handler_method(protocol.get_request_node())
    
    def get_game_version(self, proto: EAProtocol) -> int:
        if proto.model.datecode < 2016121400:
            return -1
        elif proto.model.datecode >= 2016121400 and proto.model.datecode <= 2018082100:
            return PopnConstants.VER_USANEKO
        elif proto.model.datecode > 2018082100 and proto.model.datecode <= 2020092800:
            return PopnConstants.VER_PEACE
        elif proto.model.datecode > 2020092800 and proto.model.datecode <= 2022090500:
            return PopnConstants.VER_KAIMEI
        elif proto.model.datecode > 2022090500 and proto.model.datecode < 2024010100:
            return PopnConstants.VER_UNILAB
        elif proto.model.datecode >= 2024010100 and proto.model.datecode < 2025010100:
            return PopnConstants.VER_JAM_FIZZ
        elif proto.model.datecode >= 2025010100:
            return PopnConstants.VER_HI_CHEERS
        else:
            return -2
