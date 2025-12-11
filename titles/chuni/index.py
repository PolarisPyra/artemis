import json
import logging
import re
import zlib
from logging.handlers import TimedRotatingFileHandler
from os import path
from typing import Dict, List, Tuple

import coloredlogs
import inflection
import yaml
from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from core import CoreConfig, Utils
from core.data import Data
from core.title import BaseServlet

from .air import ChuniAir
from .airplus import ChuniAirPlus
from .amazon import ChuniAmazon
from .amazonplus import ChuniAmazonPlus
from .base import ChuniBase
from .config import ChuniConfig
from .const import ChuniConstants
from .crystal import ChuniCrystal
from .crystalplus import ChuniCrystalPlus
from .luminous import ChuniLuminous
from .luminousplus import ChuniLuminousPlus
from .new import ChuniNew
from .newplus import ChuniNewPlus
from .paradise import ChuniParadise
from .plus import ChuniPlus
from .star import ChuniStar
from .starplus import ChuniStarPlus
from .sun import ChuniSun
from .sunplus import ChuniSunPlus
from .verse import ChuniVerse
from .xverse import ChuniXVerse
from .xversex import ChuniXVerseX

HONEYPOT_HEADER_NAME = "X-Cozynet-Version"
STRICT_UNDERSCORE_RE = re.compile(r"([A-Z])([A-Z])")


def strict_underscore(name: str) -> str:
    # Insert underscores between *all* capital letters
    name = STRICT_UNDERSCORE_RE.sub(r"\1_\2", name)
    return inflection.underscore(name)


class ChuniServlet(BaseServlet):
    def __init__(self, core_cfg: CoreConfig, cfg_dir: str) -> None:
        super().__init__(core_cfg, cfg_dir)

        self.game_cfg = ChuniConfig()
        self.core_data = Data(core_cfg)
        self.hash_table: Dict[str, Dict[str, str]] = {}

        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"))
            )

        self.versions = [
            ChuniBase,
            ChuniPlus,
            ChuniAir,
            ChuniAirPlus,
            ChuniStar,
            ChuniStarPlus,
            ChuniAmazon,
            ChuniAmazonPlus,
            ChuniCrystal,
            ChuniCrystalPlus,
            ChuniParadise,
            ChuniNew,
            ChuniNewPlus,
            ChuniSun,
            ChuniSunPlus,
            ChuniLuminous,
            ChuniLuminousPlus,
            ChuniVerse,
            ChuniXVerse,
            ChuniXVerseX,
        ]

        version_to_internal_version = {
            ChuniConstants.GAME_CODE: {
                range(100, 105): ChuniConstants.VER_CHUNITHM,
                range(105, 110): ChuniConstants.VER_CHUNITHM_PLUS,
                range(110, 115): ChuniConstants.VER_CHUNITHM_AIR,
                range(115, 120): ChuniConstants.VER_CHUNITHM_AIR_PLUS,
                range(120, 125): ChuniConstants.VER_CHUNITHM_STAR,
                range(125, 130): ChuniConstants.VER_CHUNITHM_STAR_PLUS,
                range(130, 135): ChuniConstants.VER_CHUNITHM_AMAZON,
                range(135, 140): ChuniConstants.VER_CHUNITHM_AMAZON_PLUS,
                range(140, 145): ChuniConstants.VER_CHUNITHM_CRYSTAL,
                range(145, 150): ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS,
                range(150, 200): ChuniConstants.VER_CHUNITHM_PARADISE,
            },
            ChuniConstants.GAME_CODE_NEW: {
                range(200, 205): ChuniConstants.VER_CHUNITHM_NEW,
                range(205, 210): ChuniConstants.VER_CHUNITHM_NEW_PLUS,
                range(210, 215): ChuniConstants.VER_CHUNITHM_SUN,
                range(215, 220): ChuniConstants.VER_CHUNITHM_SUN_PLUS,
                range(220, 225): ChuniConstants.VER_CHUNITHM_LUMINOUS,
                range(225, 230): ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS,
                range(230, 240): ChuniConstants.VER_CHUNITHM_VERSE,
                range(240, 245): ChuniConstants.VER_CHUNITHM_X_VERSE,
                range(245, 250): ChuniConstants.VER_CHUNITHM_X_VERSE_X,
            },
            ChuniConstants.GAME_CODE_INT: {
                range(100, 105): ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS,  # SUPERSTAR
                range(105, 110): ChuniConstants.VER_CHUNITHM_PARADISE,  # SUPERSTAR PLUS
                range(110, 115): ChuniConstants.VER_CHUNITHM_NEW,
                range(115, 120): ChuniConstants.VER_CHUNITHM_NEW_PLUS,
                range(120, 125): ChuniConstants.VER_CHUNITHM_SUN,
                range(125, 130): ChuniConstants.VER_CHUNITHM_SUN_PLUS,
                range(130, 135): ChuniConstants.VER_CHUNITHM_LUMINOUS,
                range(135, 140): ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS,
                range(140, 150): ChuniConstants.VER_CHUNITHM_VERSE,
                range(150, 155): ChuniConstants.VER_CHUNITHM_X_VERSE,
            },
        }
        self.version_map: Dict[str, Dict[int, int]] = {
            game_code: {
                version: internal_ver
                for version_range, internal_ver in version_ranges.items()
                for version in version_range
            }
            for game_code, version_ranges in version_to_internal_version.items()
        }

        self.logger = logging.getLogger("chuni")

        if not hasattr(self.logger, "inited"):
            log_fmt_str = "[%(asctime)s] Chunithm | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)
            file_handler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.core_cfg.server.log_dir, "chuni"),
                encoding="utf8",
                when="d",
                backupCount=10,
            )

            file_handler.setFormatter(log_fmt)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_fmt)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

            self.logger.setLevel(self.game_cfg.server.loglevel)
            coloredlogs.install(
                level=self.game_cfg.server.loglevel, logger=self.logger, fmt=log_fmt_str
            )
            self.logger.inited = True

        known_iter_counts = {
            ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS: 67,
            f"{ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS}_int": 25,  # SUPERSTAR
            ChuniConstants.VER_CHUNITHM_PARADISE: 44,
            f"{ChuniConstants.VER_CHUNITHM_PARADISE}_int": 51,  # SUPERSTAR PLUS
            ChuniConstants.VER_CHUNITHM_NEW: 54,
            f"{ChuniConstants.VER_CHUNITHM_NEW}_int": 49,
            ChuniConstants.VER_CHUNITHM_NEW_PLUS: 25,
            f"{ChuniConstants.VER_CHUNITHM_NEW_PLUS}_int": 31,
            ChuniConstants.VER_CHUNITHM_SUN: 70,
            f"{ChuniConstants.VER_CHUNITHM_SUN}_int": 35,
            ChuniConstants.VER_CHUNITHM_SUN_PLUS: 36,
            f"{ChuniConstants.VER_CHUNITHM_SUN_PLUS}_int": 36,
            ChuniConstants.VER_CHUNITHM_LUMINOUS: 8,
            f"{ChuniConstants.VER_CHUNITHM_LUMINOUS}_int": 8,
            ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS: 56,
            f"{ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS}_int": 56,
            ChuniConstants.VER_CHUNITHM_VERSE: 42,
            ChuniConstants.VER_CHUNITHM_X_VERSE: 14,
            f"{ChuniConstants.VER_CHUNITHM_X_VERSE}_int": 96,
            ChuniConstants.VER_CHUNITHM_X_VERSE_X: 49,
        }

        for version, keys in self.game_cfg.crypto.keys.items():
            if len(keys) < 3:
                continue

            if isinstance(version, int):
                version_idx = version
            else:
                version_idx = int(version.split("_")[0])

            salt = bytes.fromhex(keys[2])

            if len(keys) >= 4:
                iter_count = keys[3]
            elif (iter_count := known_iter_counts.get(version)) is None:
                self.logger.error(
                    "Number of iteration rounds for version %s is not known, but it is not specified in the config",
                    version,
                )
                continue

            self.hash_table[version] = {}

            method_list = [
                method
                for method in dir(self.versions[version_idx])
                if not method.startswith("__")
            ]

            for method in method_list:
                method_fixed = inflection.camelize(method)[6:-7]

                # This only applies for CHUNITHM NEW International and later for some reason.
                # CHUNITHM SUPERSTAR (PLUS) did not add "Exp" to the endpoint when hashing.
                if (
                    isinstance(version, str)
                    and version.endswith("_int")
                    and version_idx >= ChuniConstants.VER_CHUNITHM_NEW
                ):
                    method_fixed += "C3Exp"

                hash = PBKDF2(
                    method_fixed,
                    salt,
                    128,
                    count=iter_count,
                    hmac_hash_module=SHA1,
                )

                hashed_name = hash.hex()[
                    :32
                ]  # truncate unused bytes like the game does
                self.hash_table[version][hashed_name] = method_fixed

                self.logger.debug(
                    f"Hashed v{version} method {method_fixed} with {salt} to get {hashed_name}"
                )

    @classmethod
    def is_game_enabled(
        cls, game_code: str, core_cfg: CoreConfig, cfg_dir: str
    ) -> bool:
        game_cfg = ChuniConfig()
        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"))
            )

        if not game_cfg.server.enable:
            return False

        return True

    def get_allnet_info(
        self, game_code: str, game_ver: int, keychip: str
    ) -> Tuple[str, str]:
        if game_code == ChuniConstants.GAME_CODE and (
            game_ver < 100 or game_ver >= 200
        ):
            raise ValueError(f"Invalid version for SDBT: {game_ver}")
        if game_code == ChuniConstants.GAME_CODE_NEW and game_ver < 200:
            raise ValueError(f"Invalid version for SDHD: {game_ver}")

        title_path = f"{game_code}/{game_ver}/{keychip}/"

        if (
            not self.core_cfg.server.is_using_proxy
            and Utils.get_title_port(self.core_cfg) != 80
        ):
            return (
                f"http://{self.core_cfg.server.hostname}:{Utils.get_title_port(self.core_cfg)}/{title_path}",
                self.core_cfg.server.hostname,
            )

        return (
            f"http://{self.core_cfg.server.hostname}/{title_path}",
            self.core_cfg.server.hostname,
        )

    def get_routes(self) -> List[Route]:
        return [
            Route(
                "/{game:str}/{version:int}/{keychip:str}/ChuniServlet/{endpoint:str}",
                self.render_POST,
                methods=["POST"],
            ),
            Route(
                "/{game:str}/{version:int}/{keychip:str}/ChuniServlet/MatchingServer/{endpoint:str}",
                self.render_POST,
                methods=["POST"],
            ),
        ]

    async def render_POST(self, request: Request) -> Response:
        game_code: str = request.path_params["game"]
        version: int = request.path_params["version"]
        keychip: str = request.path_params["keychip"]
        endpoint: str = request.path_params["endpoint"]

        client_ip = Utils.get_ip_addr(request)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Encoding": "deflate",
        }
        default_error_response = zlib.compress(b'{"returnCode": 0}')

        if not self.core_cfg.server.allow_unregistered_serials:
            machine = await self.core_data.arcade.get_machine(keychip)

            if machine is None:
                self.logger.warning(
                    "Unrecognized serial %s attempted connecting to ChuniServlet from %s",
                    keychip,
                    client_ip,
                )
                return Response(default_error_response, headers=headers)

            # we gottem
            if HONEYPOT_HEADER_NAME in request.headers:
                arcade = await self.core_data.arcade.get_arcade(machine.arcade)

                self.logger.warning(
                    "Serial %s hit the honeypot from %s (arcade.name=%s, arcade.nickname=%s). The keychip will be removed.",
                    keychip,
                    client_ip,
                    arcade.name,
                    arcade.nickname,
                )

                await self.core_data.arcade.delete_machine(keychip)

                return Response(default_error_response, headers=headers)

            if machine.game is not None and machine.game != game_code:
                self.logger.warning(
                    "Serial %s attempted connecting to ChuniServlet with bad game ID %s (expected %s)",
                    game_code,
                    machine.game,
                )
                return Response(default_error_response, headers=headers)

            machine_data = machine.data if machine.data is not None else {}
            max_allowed_version = machine_data.get("max_chuni_version", 244)

            if max_allowed_version is not None and version > max_allowed_version:
                self.logger.warning(
                    "Serial %s attempted connecting to ChuniServlet with a higher version than allowed (%s, allowed %s)",
                    keychip,
                    version,
                    max_allowed_version,
                )
                return Response(
                    default_error_response,
                    headers={
                        **headers,
                        "X-Error-Reason": f"Missing {HONEYPOT_HEADER_NAME} header",
                    },
                )

        if endpoint.lower() == "ping":
            return Response(zlib.compress(b'{"returnCode": "1"}'), headers=headers)

        req_raw = await request.body()

        encrypted_request = request.headers.get("Chuni-Encoding") is not None
        compressed_request = request.headers.get("Content-Encoding") == "deflate"

        if game_code == ChuniConstants.GAME_CODE:
            default_internal_ver = ChuniConstants.VER_CHUNITHM_PARADISE
            version_map = self.version_map[ChuniConstants.GAME_CODE]
        elif game_code == ChuniConstants.GAME_CODE_NEW:
            default_internal_ver = ChuniConstants.VER_CHUNITHM_VERSE
            version_map = self.version_map[ChuniConstants.GAME_CODE_NEW]
        elif game_code == ChuniConstants.GAME_CODE_INT:
            default_internal_ver = ChuniConstants.VER_CHUNITHM_VERSE
            version_map = self.version_map[ChuniConstants.GAME_CODE_INT]
        else:
            self.logger.warning("Received request for unknown game code %s", game_code)
            return Response(default_error_response, headers=headers)

        internal_ver = version_map.get(version, default_internal_ver)

        if game_code == ChuniConstants.GAME_CODE_INT:
            crypto_cfg_key = f"{internal_ver}_int"
            hash_table_key = f"{internal_ver}_int"
        else:
            crypto_cfg_key = internal_ver
            hash_table_key = internal_ver

        # If we receive a Chuni-Encoding header, we're receiving an encrypted request.
        if encrypted_request:
            endpoint = endpoint.lower()

            # In CRYSTAL+/PARADISE, the endpoint name inside the user agent was not obfuscated.
            if internal_ver < ChuniConstants.VER_CHUNITHM_NEW:
                endpoint = request.headers.get("User-Agent").split("#")[0]
            elif hash_table_key not in self.hash_table:
                self.logger.error(
                    "v%s does not support encryption, or no keys were entered.", version
                )
                return Response(default_error_response, headers=headers)
            elif endpoint not in self.hash_table[hash_table_key]:
                self.logger.error(
                    "No hashes found for v%s endpoint %s", version, endpoint
                )
                return Response(default_error_response, headers=headers)
            else:
                endpoint = self.hash_table[hash_table_key][endpoint]

            try:
                crypt = AES.new(
                    bytes.fromhex(self.game_cfg.crypto.keys[crypto_cfg_key][0]),
                    AES.MODE_CBC,
                    bytes.fromhex(self.game_cfg.crypto.keys[crypto_cfg_key][1]),
                )
                req_raw = crypt.decrypt(req_raw)
            except Exception as e:
                self.logger.exception(
                    f"Failed to decrypt v{version} request to {endpoint}", exc_info=e
                )
                return Response(default_error_response, headers=headers)

        if (
            not encrypted_request
            and self.game_cfg.crypto.encrypted_only
            and internal_ver >= ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS
        ):
            self.logger.error(
                f"Unencrypted v{version} {endpoint} request, but config is set to encrypted only: {req_raw}"
            )
            return Response(default_error_response, headers=headers)

        if compressed_request:
            try:
                unzip = zlib.decompress(req_raw)
            except zlib.error as e:
                self.logger.exception(
                    "Failed to decompresss v%s %s request",
                    version,
                    endpoint,
                    exc_info=e,
                )
                return Response(default_error_response, headers=headers)
        else:
            unzip = req_raw

        try:
            req_data = json.loads(unzip)
        except json.decoder.JSONDecodeError as e:
            self.logger.exception(
                "Failed to parse v%s %s request", version, endpoint, exc_info=e
            )
            return Response(default_error_response, headers=headers)

        self.logger.info(f"v{version} {endpoint} request from {client_ip}")
        self.logger.debug("---> %s", req_data)

        if game_code == ChuniConstants.GAME_CODE_INT and version >= 110:
            endpoint = endpoint.removesuffix("C3Exp")
        elif game_code == ChuniConstants.GAME_CODE_INT and version < 110:
            endpoint = endpoint.removesuffix("Exp")

        func_to_find = "handle_" + strict_underscore(endpoint) + "_request"
        handler_cls = self.versions[internal_ver](self.core_cfg, self.game_cfg)

        if (handler := getattr(handler_cls, func_to_find, None)) is not None:
            try:
                resp = await handler(req_data)
            except Exception as e:
                self.logger.exception(
                    "Error handling v%s method %s", version, endpoint, exc_info=e
                )
                return Response(default_error_response, headers=headers)

            if resp is None:
                self.logger.warning(
                    "Handler for v%s method %s did not return a value",
                    version,
                    endpoint,
                )
                resp = {"returnCode": 1}
        else:
            self.logger.warning("Unhandled v%s request %s", version, endpoint)
            resp = {"returnCode": 1}

        self.logger.debug("<--- %s", resp)

        data = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

        if compressed_request:
            data = zlib.compress(data)
            headers["Content-Encoding"] = "deflate"

        if encrypted_request:
            crypt = AES.new(
                bytes.fromhex(self.game_cfg.crypto.keys[crypto_cfg_key][0]),
                AES.MODE_CBC,
                bytes.fromhex(self.game_cfg.crypto.keys[crypto_cfg_key][1]),
            )
            data = crypt.encrypt(pad(data, 16))
            headers["Chuni-Encoding"] = request.headers["Chuni-Encoding"]
            del headers["Content-Encoding"]

        return Response(data, headers=headers)
