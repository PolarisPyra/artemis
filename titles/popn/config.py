from core.config import CoreConfig


class PopnServerConfig:
    def __init__(self, parent_config: "PopnConfig") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "popn", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return CoreConfig.str_to_loglevel(
            CoreConfig.get_config_field(
                self.__config, "popn", "server", "loglevel", default="info"
            )
        )


class PopnConfig(dict):
    def __init__(self) -> None:
        self.server = PopnServerConfig(self)
