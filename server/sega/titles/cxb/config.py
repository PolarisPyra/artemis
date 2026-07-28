from server.sega.config import ArtemisConfig


class CxbServerConfig:
    def __init__(self, parent_config: "CxbConfig"):
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "cxb", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "cxb", "server", "loglevel", default="info"
            )
        )

    @property
    def use_https(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "cxb", "server", "use_https", default=True
        )


class CxbConfig(dict):
    def __init__(self) -> None:
        self.server = CxbServerConfig(self)
