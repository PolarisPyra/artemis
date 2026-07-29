"""Artemis e-amusement services shared by Konami game titles."""

from __future__ import annotations

import hashlib
import ipaddress
import logging
from collections.abc import Callable, Iterable
from urllib.parse import urlsplit

from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .protocol import EamuseInfo, EamuseResponse
from .router import EamuseRouter

logger = logging.getLogger("konami")


class ArtemisServices:
    """Register the protocol-level services provided by Artemis."""

    def __init__(
        self,
        cfg: ArtemisConfig,
        game_codes: tuple[str, ...] = (),
        module_provider: Callable[[str, str], Iterable[str]] | None = None,
    ) -> None:
        self.data = Data(cfg)
        self.game_codes = game_codes
        self.module_provider = module_provider

    def register(self, router: EamuseRouter) -> None:
        for game_code in self.game_codes:
            router.add(game_code, "services", "get", self.services_get)
            router.add(game_code, "facility", "get", self.facility_get)
            router.add(game_code, "message", "get", self.message_get)
            router.add(game_code, "package", "list", self.package_list)
            # These modules are part of bemaniutils' core service discovery
            # surface.  The handlers intentionally acknowledge packets only;
            # title-specific data remains in the Pop'n route set.
            for method in ("get", "getlist", "entry", "update", "delete"):
                router.add(game_code, "lobby", method, self.success)
            for method in ("get", "boot", "write"):
                router.add(game_code, "local", method, self.success)
            router.add(game_code, "pcbevent", "put", self.success)
            router.add(game_code, "dlstatus", "progress", self.success)
            router.add(game_code, "pcbtracker", "alive", self.pcbtracker_alive)
            router.add(game_code, "pkglist", "nr_entry", self.success)
            for method in ("income", "outcome", "income.sales.sale"):
                router.add(game_code, "posevent", method, self.success)
            router.add(game_code, "eacoin", "checkout", self.success)
            router.add(game_code, "eacoin", "checkin", self.eacoin_checkin)
            router.add(game_code, "eacoin", "consume", self.eacoin_consume)
            router.add(game_code, "eacoin", "getlog", self.success)
            router.add(game_code, "eacoin", "opcheckin", self.eacoin_checkin)
            router.add(game_code, "eacoin", "opcheckout", self.success)
            router.add(game_code, "eacoin", "opchpass", self.success)
            router.add(game_code, "cardmng", "inquire", self.card_inquire)
            router.add(game_code, "cardmng", "getrefid", self.card_getrefid)
            router.add(game_code, "cardmng", "getdatalist", self.card_getdatalist)
            router.add(game_code, "cardmng", "getkeepspan", self.card_getkeepspan)
            router.add(game_code, "cardmng", "authpass", self.card_authpass)
            router.add(game_code, "cardmng", "bindmodel", self.card_bindmodel)

    async def services_get(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        host = info.host or self.data.config.konami.hostname or "localhost"
        if not info.proxy and ":" not in host:
            host = f"{host}:{self.data.config.konami.port}"
        keepalive_host = self._keepalive_host(info, host)
        modules = [
            "cardmng",
            "dlstatus",
            "eacoin",
            "facility",
            "lobby",
            "local",
            "message",
            "package",
            "pcbevent",
            "pcbtracker",
            "pkglist",
            "posevent",
        ]
        if self.module_provider is not None:
            modules.extend(self.module_provider(info.game_code, info.model))
        # Preserve declaration order while avoiding duplicate service entries.
        modules = list(dict.fromkeys(modules))
        service_url = f"{info.protocol}://{host}/"
        response.content = {
            "@attr": {
                "expire": "600",
                "method": "get",
                "mode": "operation",
                "product_domain": "1",
            },
            "item": [
                {"@attr": {"name": name, "url": service_url}}
                for name in modules
            ],
        }
        response.content["item"].extend([
            {"@attr": {"name": "ntp", "url": "ntp://pool.ntp.org/"}},
            {
                "@attr": {
                    "name": "keepalive",
                    "url": f"{info.protocol}://{keepalive_host}/core/keepalive?pa={keepalive_host}&ia={keepalive_host}&ga={keepalive_host}&ma={keepalive_host}&t1=2&t2=10",
                }
            },
        ])
        logger.info(
            "services advertise game=%s url=%s modules=%s",
            info.game_code,
            service_url,
            len(modules) + 2,
        )

    def _keepalive_host(self, info: EamuseInfo, advertised_host: str) -> str:
        """Choose a keepalive endpoint reachable from the cabinet.

        The historical default is loopback, which is correct for a local
        cabinet but makes a remote client stop after ``services.get``: it
        contacts its own loopback interface instead of Artemis.  Preserve an
        explicitly configured non-loopback target and local behavior.
        """
        configured = str(self.data.config.konami.ping_ip or "127.0.0.1")
        try:
            configured_ip = ipaddress.ip_address(configured)
        except ValueError:
            return configured
        if not configured_ip.is_loopback or not info.client_ip:
            return configured
        try:
            client_ip = ipaddress.ip_address(info.client_ip)
        except ValueError:
            return configured
        if client_ip.is_loopback:
            return configured
        advertised = advertised_host or info.host or self.data.config.konami.hostname
        if not advertised:
            return configured
        if not info.proxy:
            return advertised
        host = urlsplit(f"//{advertised}").hostname
        return host or configured

    async def facility_get(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
            "@attr": {"expire": "600"},
            "location": {
                "id": _item("str", "ea"),
                "country": _item("str", "JP"),
                "region": _item("str", "JP-13"),
                "name": _item("str", "ARTEMIS"),
                "type": _item("u8", 0),
                "countryname": _item("str", "UNKNOWN"),
                "countryjname": _item("str", "不明"),
                "regionname": _item("str", "ARTEMIS"),
                "regionjname": _item("str", "ARTEMIS"),
                "customercode": _item("str", "AXUSR"),
                "companycode": _item("str", "AXCPY"),
                "latitude": _item("s32", 6666),
                "longitude": _item("s32", 6666),
                "accuracy": _item("u8", 0),
            },
            "line": {"id": _item("str", "."), "class": _item("u8", 0)},
            "portfw": {
                "globalip": _item("ip4", _ip4(info.client_ip)),
                "globalport": _item("u16", self.data.config.konami.matching_port),
                "privateport": _item("u16", self.data.config.konami.matching_port),
            },
            "public": {
                "flag": _item("u8", 1),
                "name": _item("str", "."),
                "latitude": _item("str", "0"),
                "longitude": _item("str", "0"),
            },
            "share": {
                "eacoin": {
                    "notchamount": _item("s32", 3000),
                    "notchcount": _item("s32", 3),
                    "supplylimit": _item("s32", 10000),
                },
                "url": {
                    "eapass": _item("str", "ARTEMIS"),
                    "arcadefan": _item("str", "ARTEMIS"),
                    "konaminetdx": _item("str", "ARTEMIS"),
                    "konamiid": _item("str", "ARTEMIS"),
                    "eagate": _item("str", "ARTEMIS"),
                },
                "eapass": {"valid": _item("u16", 365)},
            },
        }

    async def message_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"@attr": {"expire": "600"}}
        if self.data.config.konami.maintenance_mode:
            response.content["item"] = [
                {"@attr": {"start": "0", "end": "86400", "name": "sys.mainte"}},
                {"@attr": {"start": "0", "end": "86400", "name": "sys.eacoin.mainte"}},
            ]

    async def package_list(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        """Report that no package updates are available."""
        response.content = {"@attr": {"expire": "600"}}

    async def pcbtracker_alive(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
            "@attr": {
                "ecenable": "1" if self.data.config.konami.enable_paseli else "0",
                "expire": "600",
            }
        }

    async def eacoin_checkin(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
            "balance": {"@attr": {"__type": "s32"}, "@content": [88410]},
            "sessid": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"},
            "acstatus": {"@attr": {"__type": "u8"}, "@content": [0]},
            "sequence": {"@attr": {"__type": "s16"}, "@content": [1]},
            "acid": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"},
            "acname": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"},
        }

    async def eacoin_consume(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
            "autocharge": {"@attr": {"__type": "u8"}, "@content": [0]},
            "acstatus": {"@attr": {"__type": "u8"}, "@content": [0]},
            "balance": {"@attr": {"__type": "s32"}, "@content": [88410]},
        }

    async def success(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.status = 0

    async def card_inquire(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        cardid = data.get("@attr", {}).get("cardid", "")
        refid = self._refid(cardid)
        profile = await self._card_profile(refid, info.game_code)
        if profile is None or profile.get("pin", "unset") == "unset":
            response.status = 112
            return
        bound = await self.data.konami.get_extid(refid, info.game_code)
        response.content = {
            "@attr": {
                "binded": "1" if bound is not None else "0",
                "dataid": refid,
                "ecflag": "1",
                "expired": "0",
                "newflag": "0",
                "refid": refid,
            }
        }

    async def card_getrefid(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        cardid = data.get("@attr", {}).get("cardid", "")
        refid = self._refid(cardid)
        profile = await self._card_profile(refid, info.game_code)
        if profile is None:
            profile = {
                "collection": "profile",
                "name": "ゲスト",
                "friendId": _friend_id(refid),
                "dataVersion": 2,
                "pin": data.get("@attr", {}).get("passwd", "unset"),
            }
        else:
            # Treat getrefid on an existing card as the PIN update operation,
            # rather than silently retaining the old PIN.
            profile["pin"] = data.get("@attr", {}).get(
                "passwd", profile.get("pin", "unset")
            )
        await self.data.konami.put_profile(refid, profile)
        await self.data.konami.put_card(cardid, refid)
        extid = self.data.konami._stable_id(f"extid:{info.game_code}:{refid}") % 100000000
        await self.data.konami.put_extid(refid, info.game_code, extid)
        response.content = {"@attr": {"dataid": refid, "refid": refid}}

    async def card_authpass(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        refid = data.get("@attr", {}).get("refid", "DEADC0DEFEEDBEEF")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 110
        elif str(profile.get("pin", "unset")) != str(
            data.get("@attr", {}).get("pass", "-1")
        ):
            response.status = 116

    async def card_bindmodel(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        refid = data.get("@attr", {}).get("refid", "")
        if refid:
            profile = await self._card_profile(refid, info.game_code)
            if profile is not None:
                extid = self.data.konami._stable_id(
                    f"extid:{info.game_code}:{refid}"
                ) % 100000000
                await self.data.konami.put_extid(refid, info.game_code, extid)
        response.content = {"@attr": {"dataid": refid}}

    async def _card_profile(self, refid: str, game_code: str) -> dict | None:
        """Read and migrate a card profile across Pop'n version namespaces."""
        profile = await self.data.konami.get_profile(refid)
        if profile is not None:
            return profile
        for namespace in dict.fromkeys((game_code, "M39")):
            profile = await self.data.konami.get_document(
                refid, namespace, "profile"
            )
            if profile is not None:
                await self.data.konami.put_profile(refid, profile)
                return profile
        return None

    async def card_getdatalist(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        """Return an empty card data list for the initial card flow."""
        response.content = {"card": []}

    async def card_getkeepspan(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        """Return the standard profile retention period expected by EA3 clients."""
        response.content = {"@attr": {"keepspan": "30"}}

    @staticmethod
    def _refid(cardid: str) -> str:
        return (
            hashlib.sha256(f"artemis-konami:{cardid}".encode()).hexdigest()[:16].upper()
        )


def _item(type_name: str, value):
    return {
        "@attr": {"__type": type_name},
        "@content": [value] if type_name != "str" else value,
    }


def _ip4(value: str) -> int:
    try:
        parts = [int(part) for part in value.split(".")]
        if len(parts) != 4 or any(part < 0 or part > 255 for part in parts):
            return 0
        result = 0
        for part in parts:
            result = (result << 8) | part
        return result
    except (TypeError, ValueError):
        return 0


def _friend_id(refid: str) -> str:
    value = int(hashlib.sha256(f"friend:{refid}".encode()).hexdigest()[:12], 16)
    return f"{value % 1_000_000_000_000:012d}"
