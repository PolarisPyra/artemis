from typing import Dict, Optional

from artemis.config import ArtemisConfig


class Mai2ServerConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "mai2", "server", "loglevel", default="info"
            )
        )


class Mai2DeliverConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "deliver", "enable", default=False
        )

    @property
    def udbdl_enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "deliver", "udbdl_enable", default=False
        )

    @property
    def content_folder(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "deliver", "content_folder", default=""
        )


class Mai2UploadsConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def photos(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "uploads", "photos", default=False
        )

    @property
    def photos_dir(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "uploads", "photos_dir", default=""
        )

    @property
    def movies(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "uploads", "movies", default=False
        )

    @property
    def movies_dir(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "uploads", "movies_dir", default=""
        )


class Mai2CryptoConfig:
    def __init__(self, parent_config: "Mai2Config") -> None:
        self.__config = parent_config

    @property
    def keys(self) -> Dict[int, list[str]]:
        """
        in the form of:
        internal_version: [key, iv, salt]
        key and iv are hex strings
        salt is a normal UTF-8 string
        """
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "crypto", "keys", default={}
        )

    @property
    def encrypted_only(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "crypto", "encrypted_only", default=False
        )


class Mai2ReadConfig:
    def __init__(self, parent_config: "Mai2Config") -> None:
        self.__config = parent_config

    @property
    def asset_hmac_key(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "read", "asset_hmac_key", default=None
        )


class Mai2OnlineChartsConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "chart_deliver", "enable", default=False
        )

    @property
    def chart_folder(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "mai2", "chart_deliver", "chart_folder", default=""
        )


class Mai2Config(dict):
    def __init__(self) -> None:
        self.server = Mai2ServerConfig(self)
        self.deliver = Mai2DeliverConfig(self)
        self.uploads = Mai2UploadsConfig(self)
        self.crypto = Mai2CryptoConfig(self)
        self.read = Mai2ReadConfig(self)
        self.charts = Mai2OnlineChartsConfig(self)
