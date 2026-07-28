"""Built-in e-amusement services shared by Konami game titles."""

from __future__ import annotations

import hashlib

from core.config import CoreConfig
from core.data import Data
from .protocol import EamuseInfo, EamuseResponse
from .router import EamuseRouter, KonamiPlugin


class CoreKonamiPlugin(KonamiPlugin):
    """Implement the protocol-level services exposed by Asphyxia CORE."""

    def __init__(self, cfg: CoreConfig, game_codes: tuple[str, ...] = ()) -> None:
        self.data = Data(cfg)
        self.game_codes = game_codes

    def register(self, router: EamuseRouter) -> None:
        for game_code in self.game_codes:
            router.add(game_code, "services", "get", self.services_get)
            router.add(game_code, "facility", "get", self.facility_get)
            router.add(game_code, "message", "get", self.message_get)
            router.add(game_code, "package", "list", self.success)
            router.add(game_code, "pcbevent", "put", self.success)
            router.add(game_code, "pcbtracker", "alive", self.success)
            router.add(game_code, "eacoin", "checkout", self.success)
            router.add(game_code, "eacoin", "checkin", self.eacoin_checkin)
            router.add(game_code, "eacoin", "consume", self.eacoin_consume)
            router.add(game_code, "posevent", "income", self.success)
            router.add(game_code, "posevent", "outcome", self.success)
            router.add(game_code, "lobby", " services", self.success)
            router.add(game_code, "cardmng", "inquire", self.card_inquire)
            router.add(game_code, "cardmng", "getrefid", self.card_getrefid)
            router.add(game_code, "cardmng", "authpass", self.card_authpass)
            router.add(game_code, "cardmng", "bindmodel", self.card_bindmodel)
            router.fallback(game_code, self.success)

    async def services_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        host = info.host or "localhost"
        response.content = {"item": [
            {"@attr": {"name": name, "url": f"{info.protocol}://{host}"}}
            for name in ("ntp", "keepalive", "cardmng", "facility", "message", "services", "package", "pcbevent", "pcbtracker", "pkglist", "posevent", "userdata", "userid", "eacoin", "local", "local2", "lobby", "lobby2", "dlstatus", "netlog", "sidmgr", "globby")
        ]}

    async def facility_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"location": {"@attr": {"id": "ea", "country": "JP", "region": "JP-13", "name": "ARTEMIS"}}}

    async def message_get(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"@attr": {"expire": "300"}}

    async def eacoin_checkin(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"balance": {"@attr": {"__type": "s32"}, "@content": [88410]}, "sessid": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"}, "acstatus": {"@attr": {"__type": "u8"}, "@content": [0]}, "sequence": {"@attr": {"__type": "s16"}, "@content": [1]}, "acid": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"}, "acname": {"@attr": {"__type": "str"}, "@content": "DEADC0DEFEEDBEEF"}}

    async def eacoin_consume(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.content = {"autocharge": {"@attr": {"__type": "u8"}, "@content": [0]}, "acstatus": {"@attr": {"__type": "u8"}, "@content": [0]}, "balance": {"@attr": {"__type": "s32"}, "@content": [88410]}}

    async def success(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        response.status = 0

    async def card_inquire(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        cardid = data.get("@attr", {}).get("cardid", "")
        refid = self._refid(cardid)
        profile = await self.data.konami.get_document(refid, info.game_code, "profile")
        if profile is None:
            response.status = 112
            return
        response.content = {"@attr": {"binded": "1", "dataid": refid, "ecflag": "1", "expired": "0", "newflag": "0", "refid": refid}}

    async def card_getrefid(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        cardid = data.get("@attr", {}).get("cardid", "")
        refid = self._refid(cardid)
        profile = await self.data.konami.get_document(refid, info.game_code, "profile")
        if profile is None:
            profile = {"collection": "profile", "name": "ゲスト", "friendId": "000000000000", "dataVersion": 2, "pin": data.get("@attr", {}).get("passwd", "unset")}
            await self.data.konami.put_document(refid, info.game_code, "profile", profile)
        response.content = {"@attr": {"dataid": refid, "refid": refid}}

    async def card_authpass(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        refid = data.get("@attr", {}).get("refid", "")
        profile = await self.data.konami.get_document(refid, info.game_code, "profile")
        if profile is None:
            response.status = 110
        elif str(profile.get("pin", "unset")) != str(data.get("@attr", {}).get("pass", "-1")):
            response.status = 116

    async def card_bindmodel(self, info: EamuseInfo, data: dict, response: EamuseResponse):
        refid = data.get("@attr", {}).get("refid", "")
        response.content = {"@attr": {"dataid": refid}}

    @staticmethod
    def _refid(cardid: str) -> str:
        return hashlib.sha256(f"artemis-konami:{cardid}".encode()).hexdigest()[:16].upper()
