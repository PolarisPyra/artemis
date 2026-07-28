"""Artemis e-amusement services shared by Konami game titles."""

from __future__ import annotations

import hashlib
import time

from artemis.config import ArtemisConfig
from artemis.data import Data
from .protocol import EamuseInfo, EamuseResponse
from .router import EamuseRouter


class ArtemisServices:
    """Register the protocol-level services provided by Artemis."""

    def __init__(self, cfg: ArtemisConfig, game_codes: tuple[str, ...] = ()) -> None:
        self.data = Data(cfg)
        self.game_codes = game_codes
        self.profile_code = (
            "M39" if "M39" in game_codes else game_codes[0] if game_codes else ""
        )

    def register(self, router: EamuseRouter) -> None:
        for game_code in self.game_codes:
            router.add(game_code, "services", "get", self.services_get)
            router.add(game_code, "facility", "get", self.facility_get)
            router.add(game_code, "message", "get", self.message_get)
            router.add(game_code, "package", "list", self.success)
            router.add(game_code, "pcbevent", "put", self.success)
            router.add(game_code, "tax", "get_phase", self.tax_get_phase)
            router.add(game_code, "dlstatus", "progress", self.success)
            router.add(game_code, "pcbtracker", "alive", self.pcbtracker_alive)
            router.add(game_code, "eacoin", "checkout", self.success)
            router.add(game_code, "eacoin", "checkin", self.eacoin_checkin)
            router.add(game_code, "eacoin", "consume", self.eacoin_consume)
            router.add(game_code, "posevent", "income", self.posevent_income)
            router.add(
                game_code,
                "posevent",
                "income.sales.sale",
                self.posevent_sale,
            )
            router.add(game_code, "posevent", "outcome", self.success)
            router.add(game_code, "lobby", "get", self.success)
            router.add(game_code, "cardmng", "inquire", self.card_inquire)
            router.add(game_code, "cardmng", "getrefid", self.card_getrefid)
            router.add(game_code, "cardmng", "authpass", self.card_authpass)
            router.add(game_code, "cardmng", "bindmodel", self.card_bindmodel)
            router.fallback(game_code, self.success)

    async def services_get(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        host = info.host or "localhost"
        if not info.proxy and ":" not in host:
            host = f"{host}:{self.data.config.konami.port}"
        response.content = {
            "@attr": {"expire": "10800", "method": "get", "mode": "operation"},
            "item": [
                {"@attr": {"name": name, "url": f"{info.protocol}://{host}"}}
                for name in (
                    "cardmng",
                    "facility",
                    "message",
                    "numbering",
                    "package",
                    "pcbevent",
                    "pcbtracker",
                    "pkglist",
                    "posevent",
                    "userdata",
                    "userid",
                    "eacoin",
                    "local",
                    "local2",
                    "lobby",
                    "lobby2",
                    "dlstatus",
                    "netlog",
                    "sidmgr",
                    "globby",
                )
            ],
        }
        response.content["item"][:0] = [
            {"@attr": {"name": "ntp", "url": "ntp://pool.ntp.org/"}},
            {
                "@attr": {
                    "name": "keepalive",
                    "url": f"{info.protocol}://{host}/keepalive?pa={self.data.config.konami.ping_ip}&ia={self.data.config.konami.ping_ip}&ga={self.data.config.konami.ping_ip}&ma={self.data.config.konami.ping_ip}&t1=2&t2=10",
                }
            },
        ]

    async def facility_get(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
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
                "name": _item("str", "UNKNOWN"),
                "latitude": _item("str", "0"),
                "longitude": _item("str", "0"),
            },
            "share": {
                "eacoin": {
                    "notchamount": _item("s32", 0),
                    "notchcount": _item("s32", 0),
                    "supplylimit": _item("s32", 100000),
                },
                "url": {
                    "eapass": _item("str", "ARTEMIS"),
                    "arcadefan": _item("str", "ARTEMIS"),
                    "konaminetdx": _item("str", "ARTEMIS"),
                    "konamiid": _item("str", "ARTEMIS"),
                    "eagate": _item("str", "ARTEMIS"),
                },
            },
        }

    async def message_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"@attr": {"expire": "300"}}
        if self.data.config.konami.maintenance_mode:
            response.content["item"] = [
                {"@attr": {"start": "0", "end": "86400", "name": "sys.mainte"}},
                {"@attr": {"start": "0", "end": "86400", "name": "sys.eacoin.mainte"}},
            ]

    async def tax_get_phase(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {"phase": _item("s32", 0)}

    async def pcbtracker_alive(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = {
            "@attr": {
                "ecenable": "1" if self.data.config.konami.enable_paseli else "0",
                "eclimit": "0",
                "expire": "1200",
                "limit": "0",
                "time": str(int(time.time())),
            }
        }

    async def posevent_sale(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        response.content = [
            {"@attr": {"status": "0"}},
            {"@attr": {"status": "0"}},
            {"@attr": {"status": "0"}},
        ]

    async def posevent_income(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ):
        if "sales" in data:
            await self.posevent_sale(info, data, response)
        else:
            await self.success(info, data, response)

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
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            profile = await self.data.konami.get_document(refid, self.profile_code, "profile")
            if profile is not None:
                await self.data.konami.put_profile(refid, profile)
        if profile is None or profile.get("pin", "unset") == "unset":
            response.status = 112
            return
        response.content = {
            "@attr": {
                "binded": "1",
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
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            profile = await self.data.konami.get_document(refid, self.profile_code, "profile")
        if profile is None:
            profile = {
                "collection": "profile",
                "name": "ゲスト",
                "friendId": "000000000000",
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
        extid = self.data.konami._stable_id(f"extid:{self.profile_code}:{refid}") % 100000000
        await self.data.konami.put_extid(refid, self.profile_code, extid)
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
        response.content = {"@attr": {"dataid": refid}}

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
