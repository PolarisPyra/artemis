import logging
import os
import ssl
from typing import Any, Union

from typing_extensions import Optional


class ServerConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def listen_address(self) -> str:
        """
        Address Artemis will bind to and listen on
        """
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "listen_address", default="127.0.0.1"
        )

    @property
    def hostname(self) -> str:
        """
        Hostname sent to games
        """
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "hostname", default="localhost"
        )

    @property
    def port(self) -> int:
        """
        Port the game will listen on
        """
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "port", default=80
        )

    @property
    def ssl_key(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "ssl_key", default="cert/title.key"
        )

    @property
    def ssl_cert(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "title", "ssl_cert", default="cert/title.pem"
        )

    @property
    def allow_user_registration(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "allow_user_registration", default=True
        )

    @property
    def allow_unregistered_serials(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "allow_unregistered_serials", default=True
        )

    @property
    def name(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "name", default="ARTEMiS"
        )

    @property
    def is_develop(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "is_develop", default=True
        )

    @property
    def is_using_proxy(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "is_using_proxy", default=False
        )

    @property
    def proxy_port(self) -> int:
        """
        What port the proxy is listening on. This will be sent instead of 'port' if
        is_using_proxy is True and this value is non-zero
        """
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "proxy_port", default=0
        )

    @property
    def proxy_port_ssl(self) -> int:
        """
        What port the proxy is listening for secure connections on. This will be sent
        instead of 'port' if is_using_proxy is True and this value is non-zero
        """
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "proxy_port_ssl", default=0
        )

    @property
    def log_dir(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "log_dir", default="logs"
        )

    @property
    def check_arcade_ip(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "check_arcade_ip", default=False
        )

    @property
    def strict_ip_checking(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "server", "strict_ip_checking", default=False
        )


class TitleConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "title", "loglevel", default="info"
            )
        )

    @property
    def reboot_start_time(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "title", "reboot_start_time", default=""
        )

    @property
    def reboot_end_time(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "title", "reboot_end_time", default=""
        )


class DatabaseConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def host(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "host", default="localhost"
        )

    @property
    def username(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "username", default="aime"
        )

    @property
    def password(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "password", default="aime"
        )

    @property
    def name(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "name", default="aime"
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "port", default=3306
        )

    @property
    def protocol(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "protocol", default="mysql"
        )

    @property
    def ssl_enabled(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_enabled", default=False
        )

    @property
    def ssl_cafile(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_cafile", default=None
        )

    @property
    def ssl_capath(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_capath", default=None
        )

    @property
    def ssl_cert(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_cert", default=None
        )

    @property
    def ssl_key(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_key", default=None
        )

    @property
    def ssl_key_password(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_key_password", default=None
        )

    @property
    def ssl_verify_identity(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_verify_identity", default=True
        )

    @property
    def ssl_verify_cert(self) -> Optional[Union[str, bool]]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_verify_cert", default=None
        )

    @property
    def ssl_ciphers(self) -> Optional[str]:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "ssl_ciphers", default=None
        )

    @property
    def sha2_password(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "sha2_password", default=False
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "database", "loglevel", default="info"
            )
        )

    @property
    def enable_memcached(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "enable_memcached", default=True
        )

    @property
    def memcached_host(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "database", "memcached_host", default="localhost"
        )

    def create_ssl_context_if_enabled(self):
        if not self.ssl_enabled:
            return

        no_ca = self.ssl_cafile is None and self.ssl_capath is None

        ctx = ssl.create_default_context(
            cafile=self.ssl_cafile,
            capath=self.ssl_capath,
        )
        ctx.check_hostname = not no_ca and self.ssl_verify_identity

        if self.ssl_verify_cert is None:
            ctx.verify_mode = ssl.CERT_NONE if no_ca else ssl.CERT_REQUIRED
        elif isinstance(self.ssl_verify_cert, bool):
            ctx.verify_mode = (
                ssl.CERT_REQUIRED if self.ssl_verify_cert else ssl.CERT_NONE
            )
        elif isinstance(self.ssl_verify_cert, str):
            value = self.ssl_verify_cert.lower()

            if value in ("none", "0", "false", "no"):
                ctx.verify_mode = ssl.CERT_NONE
            elif value == "optional":
                ctx.verify_mode = ssl.CERT_OPTIONAL
            elif value in ("required", "1", "true", "yes"):
                ctx.verify_mode = ssl.CERT_REQUIRED
            else:
                ctx.verify_mode = ssl.CERT_NONE if no_ca else ssl.CERT_REQUIRED

        if self.ssl_cert:
            ctx.load_cert_chain(
                self.ssl_cert,
                self.ssl_key,
                self.ssl_key_password,
            )

        if self.ssl_ciphers:
            ctx.set_ciphers(self.ssl_ciphers)

        return ctx


class FrontendConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "frontend", "enable", default=False
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "frontend", "port", default=8080
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "frontend", "loglevel", default="info"
            )
        )

    @property
    def secret(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "frontend", "secret", default=""
        )


class AllnetConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def standalone(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "allnet", "standalone", default=False
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "allnet", "port", default=80
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "allnet", "loglevel", default="info"
            )
        )

    @property
    def allow_online_updates(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "allnet", "allow_online_updates", default=False
        )

    @property
    def update_cfg_folder(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "allnet", "update_cfg_folder", default=""
        )


class BillingConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def standalone(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "billing", "standalone", default=True
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "billing", "loglevel", default="info"
            )
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "billing", "port", default=8443
        )

    @property
    def ssl_key(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "billing", "ssl_key", default="cert/server.key"
        )

    @property
    def ssl_cert(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "billing", "ssl_cert", default="cert/server.pem"
        )

    @property
    def signing_key(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "billing", "signing_key", default="cert/billing.key"
        )


class AimedbConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "enable", default=True
        )

    @property
    def listen_address(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "listen_address", default=""
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "aimedb", "loglevel", default="info"
            )
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "port", default=22345
        )

    @property
    def key(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "key", default=""
        )

    @property
    def id_secret(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "id_secret", default=""
        )

    @property
    def id_lifetime_seconds(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "aimedb", "id_lifetime_seconds", default=86400
        )


class MuchaConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "mucha", "loglevel", default="info"
            )
        )


class KonamiConfig:
    """Configuration for Artemis' native e-amusement service."""

    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def db_host(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "host",
            default=self.__config.database.host,
        )

    @property
    def db_username(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "username",
            default=self.__config.database.username,
        )

    @property
    def db_password(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "password",
            default=self.__config.database.password,
        )

    @property
    def db_name(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami_database", "name", default="konami"
        )

    @property
    def db_port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "port",
            default=self.__config.database.port,
        )

    @property
    def db_protocol(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "protocol",
            default=self.__config.database.protocol,
        )

    @property
    def db_sha2_password(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config,
            "artemis",
            "konami_database",
            "sha2_password",
            default=self.__config.database.sha2_password,
        )

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "enable", default=False
        )

    @property
    def standalone(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "standalone", default=False
        )

    @property
    def port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "port", default=5730
        )

    @property
    def hostname(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "hostname", default="localhost"
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "konami", "loglevel", default="info"
            )
        )

    @property
    def popn_force_unlock(self) -> bool:
        enabled = ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "enable_force_unlock", default=None
        )
        if enabled is not None:
            return enabled
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "popn_force_unlock", default=True
        )

    @property
    def enable_score_sharing(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "enable_score_sharing", default=True
        )

    @property
    def ping_ip(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "ping_ip", default="127.0.0.1"
        )

    @property
    def matching_port(self) -> int:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "matching_port", default=5700
        )

    @property
    def enable_paseli(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "enable_paseli", default=True
        )

    @property
    def maintenance_mode(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "konami", "maintenance_mode", default=False
        )


class ChimedbConfig:
    def __init__(self, parent_config: "ArtemisConfig") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "chimedb", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return ArtemisConfig.str_to_loglevel(
            ArtemisConfig.get_config_field(
                self.__config, "artemis", "chimedb", "loglevel", default="info"
            )
        )

    @property
    def key(self) -> str:
        return ArtemisConfig.get_config_field(
            self.__config, "artemis", "chimedb", "key", default=""
        )


class ArtemisConfig(dict):
    def __init__(self) -> None:
        self.server = ServerConfig(self)
        self.title = TitleConfig(self)
        self.database = DatabaseConfig(self)
        self.frontend = FrontendConfig(self)
        self.allnet = AllnetConfig(self)
        self.billing = BillingConfig(self)
        self.aimedb = AimedbConfig(self)
        self.chimedb = ChimedbConfig(self)
        self.mucha = MuchaConfig(self)
        self.konami = KonamiConfig(self)

    @classmethod
    def str_to_loglevel(cls, level_str: str):
        if level_str.lower() == "error":
            return logging.ERROR
        elif level_str.lower().startswith("warn"):  # Fits warn or warning
            return logging.WARN
        elif level_str.lower() == "debug":
            return logging.DEBUG
        else:
            return logging.INFO

    @classmethod
    def loglevel_to_str(cls, level: int) -> str:
        if level == logging.ERROR:
            return "error"
        elif level == logging.WARN:
            return "warn"
        elif level == logging.INFO:
            return "info"
        elif level == logging.DEBUG:
            return "debug"
        else:
            return "notset"

    @classmethod
    def get_config_field(
        cls, __config: dict, module, *path: str, default: Any = ""
    ) -> Any:
        envKey = f"CFG_{module}_"
        for arg in path:
            envKey += arg + "_"

        if envKey.endswith("_"):
            envKey = envKey[:-1]

        if envKey in os.environ:
            return os.environ.get(envKey)

        read = __config

        for x in range(len(path) - 1):
            read = read.get(path[x], {})

        return read.get(path[len(path) - 1], default)
