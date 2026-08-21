from typing import Union, Tuple, Dict, List
from types import ModuleType
from typing_extensions import Final
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
import logging
import coloredlogs
from logging.handlers import TimedRotatingFileHandler
import re
from datetime import datetime
import traceback
import sys

from core import CoreConfig, Utils
from core.const import AllnetCountryCode, EaCountryCode
from core.data import Data
from .eaapi.node import XMLNode, Type
from .eaapi.misc import parse_model
from .eaapi.crypt import ea_symmetric_crypt
from .eaapi.lz77 import lz77_decompress
from .eaapi.decoder import Decoder
from .eaapi.encoder import Encoder
from .eaapi.exception import InvalidModel
from .eaapi.const import FAULT_MALFORMED_REQUEST, FAULT_BAD_GAME, FAULT_EA_REGISTRATION_NEEDED, FAULT_GAME_UNSUPORTED, FAULT_GAME_OLD
from .eaapi.cardconv import uid_to_konami

# The cabinet expects this signed 32-bit display value for an unlimited wallet.
# Finite wallets use their database balance instead.
INFINITE_PASELI_BALANCE: Final[int] = 5730

class EAModel:
    def __init__(self, model: str) -> None:
        match = re.match(
            r"^([A-Z0-9]{3}):([A-Z]):([A-Z]):([A-Z])(?::(\d{8,10}))?$", model
        )
        if match is None:
            raise InvalidModel
        self.gamecode, self.dest, self.spec, self.rev, self.datecode = match.groups()

        if len(self.datecode) == 8:
            self.datecode += "00"
        self.datecode = int(self.datecode)

    def __str__(self) -> str:
        return f"{self.gamecode}:{self.dest}:{self.spec}:{self.rev}:{self.datecode}"

class EAProtocol:
    COMPRESS_TYPE_NONE: Final[int] = 0
    COMPRESS_TYPE_LZSS: Final[int] = 1

    def __init__(
        self,
        request_data: bytes,
        compress: Union[str, None],
        eamuse_info: Union[str, None],
        shared_secret: bytes,
        model: str,
        method: str,
        client_ip: str = "0.0.0.0"
    ) -> None:
        self.__req_raw = request_data
        self.__req = None

        self.__is_compressed = (
            self.COMPRESS_TYPE_LZSS if compress == "lz77" else self.COMPRESS_TYPE_NONE
        )
        self.__ea_info = eamuse_info

        self.__resp = None
        self.__resp_raw = None

        self.__shared_secret = shared_secret
        self.__key = None
        self.__xml_encoding = None

        self.logger = logging.getLogger("eamuse")

        self.model = EAModel(model)
        self.method = method

        self.pcbid = None
        self.tag = None
        self.client_ip = client_ip
        self.process_request()

    def process_request(self) -> None:
        self.logger.debug(
            f"Method {self.method} Model {self.model} compressed {self.__is_compressed} eainfo {self.__ea_info} client ip {self.client_ip}"
        )
        if self.__ea_info is not None:
            data = ea_symmetric_crypt(
                self.__req_raw, self.__ea_info, self.__shared_secret
            )
        else:
            data = self.__req_raw

        if self.__is_compressed:
            data = lz77_decompress(data)
        
        self.logger.log(5, f"Eamuse request data: {data.hex()}")

        xml = Decoder(data).unpack()
        self.logger.debug(f"Eamuse {self.model} {self.method} request")
        self.pcbid = xml.attributes.get("srcid")
        self.tag = xml.attributes.get("tag")
        self.__req = xml

        self.logger.debug(f"{xml.to_str()}")

    def get_request_node(self) -> XMLNode:
        if self.__req is None:
            raise Exception("EAProtocol: Tried to get request before it's set!")
        return self.__req

    def set_resp(self, resp: XMLNode) -> None:
        self.__resp = resp

    def get_resp_packet(self) -> bytes:
        if self.__resp_raw is None:
            if self.__resp is None:
                raise Exception(
                    "EAProtocol: Tried to get response bytes when response isn't set!"
                )

            self.logger.debug(f"Eamuse response: {self.__resp.to_str()}")
            enc = Encoder().encode(self.__resp)
            self.logger.log(5, f"Eamuse raw response {enc.hex()}")

            if self.__ea_info is not None:
                self.__resp_raw = ea_symmetric_crypt(
                    enc, self.__ea_info, self.__shared_secret
                )
            else:
                self.__resp_raw = enc
        return self.__resp_raw

class BaseDispatcher:
    def __init__(self, core_config: CoreConfig, config_dir: str) -> None:
        self.core_cfg = core_config
        self.logger = logging.getLogger("eamuse")
        self.game_cfg = None
        self.versions = []
    
    @classmethod
    def is_game_enabled(cls, game_code: str, core_cfg: CoreConfig, cfg_dir: str) -> bool:
        """Called during boot to check if a specific game code should load.

        Args:
            game_code (str): 4 character game code
            core_cfg (CoreConfig): CoreConfig class
            cfg_dir (str): Config directory

        Returns:
            bool: True if the game is enabled and set to run, False otherwise
        
        """
        return False
    
    def get_mucha_info(self, core_cfg: CoreConfig, cfg_dir: str) -> Tuple[bool, List[str], List[str]]:
        """Called once during boot to check if this game is a mucha game

        Args:
            core_cfg (CoreConfig): CoreConfig class
            cfg_dir (str): Config directory

        Returns:
            Tuple[bool, str]: Tuple where offset 0 is true if the game is enabled, false otherwise, and offset 1 is the game CD
        """
        return (False, [], [])
    
    async def dispatch(self, protocol: EAProtocol, internal_ver: int) -> XMLNode:
        func_to_find = f"handle_{protocol.method.replace('.', '_')}"

        handler_cls = self.versions[internal_ver](
            self.core_cfg, self.game_cfg, protocol
        )
        handler = getattr(handler_cls, func_to_find, None)
        if handler is not None:
            return await handler(protocol.get_request_node())

        else:
            self.logger.warning(f"{protocol.model.gamecode} does not dispatch {protocol.method}")
            return None
    
    def get_routes(self) -> List[Route]:
        """Called during boot to get all matcher endpoints this title servlet handles

        Returns:
            List[Route]: A list of Routes, WebSocketRoutes, or similar classes
        """
        return []

    def get_game_version(self, proto: EAProtocol) -> int:
        return -1

class BaseHandler:
    def __init__(self, core_config: CoreConfig, protocol: EAProtocol) -> None:
        self.core_config = core_config
        self.data = Data(core_config)
        self.logger = logging.getLogger("eamuse")
        self.extra_services = {}
        self.protocol = protocol
        self.game = None
        self.version = None

    def decode_pcbevent(self, event: str, value: int) -> str:
        evt_split = event.split(".")
        ret = None

        if evt_split[0] == "game":
            if evt_split[1] == "s":
                if len(evt_split) == 2:
                    ret = "Game started with coins"

                elif evt_split[2] == "free":
                    ret = "Game Started for Free"

                elif evt_split[2] == "ec":
                    ret = "Game Started with PASELI"

            elif evt_split[1] == "c":
                if len(evt_split) == 2:
                    ret = "Game Continued"

                elif evt_split[2] == "free":
                    ret = "Game Continued for Free"

                elif evt_split[2] == "ec":
                    ret = "Game Continued with PASELI"

            elif evt_split[1] == "e":
                ret = "Game End"

        elif evt_split[0] == "boot":
            ret = "Game Boot"

        elif evt_split[0] == "pdata":
            if evt_split[1] == "w":
                ret = "Player Data Write"
            if evt_split[1] == "r":
                ret = "Player Data Read"

        elif evt_split[0] == "update":
            if evt_split[1] == "w":
                ret = "Update Write"
            if evt_split[1] == "r":
                ret = "Update Read"

        elif evt_split[0] == "service":
            if evt_split[1] == "p":
                ret = f"{value} Service coin(s) added"

        elif evt_split[0] == "coin":
            if evt_split[1] == "i":
                ret = f"{value} Coin(s) inserted"

        if ret is None:
            return f"{value} {event}"
        return ret

    def get_previous_version(self) -> Tuple[str, int]:
        """
        Given the classes current gamecode and version,
        return the previous version and it's gamecode.
        If your game has different gamecodes for different
        versions, overwrite this method.
        """
        if self.game is not None and self.version > 0:
            return (self.game, self.version - 1)
        return (None, None)

    def decode_paseli_item(self, event: str) -> str:
        if not event: return "Unknown"
        event_spt = event.split("/")
        if not event_spt[0]:
            event_spt.pop(0)
        
        if event_spt[0] == "eacoin":
            if event_spt[1] == "start":
                return "Start"
            elif event_spt[1] == "normal_start":
                return "Normal Start"
            elif event_spt[1] == "pbstart":
                return "Premium B Start"
        
        return event

    async def check_profile(self, refid: str) -> bool:
        return False

    async def check_succession_profile(self, refid: str) -> bool:
        return False

    async def bind_profile(self, refid: str) -> None:
        return None

    async def handle_services_get(self, request: XMLNode) -> XMLNode:
        def item(name: str, url: str) -> XMLNode:
            override = self.extra_services.get(name, url)
            if not override:
                override = url
            return XMLNode("item", attributes={"name": name, "url": override})
        
        machine = await self.data.arcade.get_bemani_machine(self.protocol.pcbid)
        
        url = f"http://{self.core_config.server.hostname}:{Utils.get_title_port(self.core_config)}/"
        if self.core_config.eamuse.use_https:
            url = f"https://{self.core_config.server.hostname}:{Utils.get_title_port_ssl(self.core_config)}/"

        root = XMLNode("services")
        root.attributes["expire"] = "600"
        # This can be set to 'operation', 'debug', 'test', and 'factory'.
        root.attributes["mode"] = "operation"
        root.attributes["product_domain"] = "1"

        root.children.append(item("cardmng", url))
        root.children.append(item("dlstatus", url))
        root.children.append(item("eacoin", url))
        root.children.append(item("facility", url))
        root.children.append(item("message", url))
        root.children.append(item("package", url))
        root.children.append(item("pcbevent", url))
        root.children.append(item("pcbtracker", url))
        root.children.append(item("pkglist", url))
        root.children.append(item("posevent", url))
        for srv in self.extra_services:
            root.children.append(item(srv, url))

        root.children.append(item("ntp", "ntp://pool.ntp.org/"))

        # Translate keepalive to a raw IP because we can't give out a host here
        # ia = router ip - pulled from db
        # ga = gateway ip - set in config
        # ma = center ip - set in config
        router_ip = self.protocol.client_ip
        if machine:
            arcade = await self.data.arcade.get_arcade(machine['arcade'])
            if arcade['ip']:
                router_ip = arcade['ip']
        
        root.children.append(
            item(
                "keepalive",
                f"http://127.0.0.1/core/keepalive?pa=127.0.0.1&ia={router_ip}&ga={self.core_config.eamuse.keepalive_gateway_addr}&ma={self.core_config.eamuse.keepalive_center_addr}&t1=2&t2=10",
            )
        )
        return root

    async def handle_pcbtracker_alive(self, request: XMLNode):
        return XMLNode(
            "pcbtracker",
            Type.Void,
            attributes={
                "ecenable": "1",
                "eclimit": "0",
                "expire": "600",
                "limit": "0",
                "status": "0",
                "time": str(int(datetime.now().timestamp())),
            },
        )

    async def handle_facility_get(self, request: XMLNode) -> XMLNode:
        root = XMLNode("facility", Type.Void, attributes={"expire": "600"})
        ip_spt = self.protocol.client_ip.split(".")
        if len(ip_spt) == 4:
            ip_int = (int(ip_spt[0]) << 24) | (int(ip_spt[1]) << 16) | (int(ip_spt[2]) << 8) | (int(ip_spt[3]) << 0)
        else:
            ip_int = 0x7f000001
        
        cal = XMLNode("calendar") # Not sure if this does anything...
        cal.append("year", Type.S16, datetime.now().year)
        cal.append("holiday", Type.S16, 0)
        root.children.append(cal)
        
        loc = XMLNode("location")

        machine = await self.data.arcade.get_bemani_machine(self.protocol.pcbid)
        if machine is None:
            arcade = None
            country = "JP"
            region = "JP-1"
            name = "ARTEMiS"
            mech_data = {}
            country_ea = EaCountryCode.JAPAN

        else:
            if machine["arcade"] is not None:
                arcade = await self.data.arcade.get_arcade(machine["arcade"])
            else:
                arcade = None

            country = machine["country"]
            if country is None:
                country = arcade['country']
            
            if country is None:
                country == "JP"
            
            try:
                country_ea = EaCountryCode.from_allnet(AllnetCountryCode(country))
                if country_ea is None:
                    country_ea = EaCountryCode.JAPAN
            except:
                country_ea = EaCountryCode.JAPAN

            if country_ea == EaCountryCode.JAPAN:
                ac_region = arcade['region_id']
                if ac_region is None:
                    ac_region = 1

                region = f"JP-{ac_region}"
            else:
                region = ""

            name = machine['name'] if machine['name'] else arcade['name']
            mech_data = machine['data'] if machine['data'] else {}
            
            if name is None:
                name = "ARTEMiS"

        loc.append("id", Type.Str, f"{country_ea.value}-{arcade['id']}" if machine else f"JP-0")
        loc.append("country", Type.Str, country_ea.value)
        loc.append("region", Type.Str, region)
        loc.append("name", Type.Str, name)
        loc.append("type", Type.U8, 0)
        loc.append("countryname", Type.Str, country_ea.name)
        loc.append("countryjname", Type.Str, country_ea.name)
        loc.append("regionname", Type.Str, country_ea.value)
        loc.append("regionjname", Type.Str, country_ea.value)
        loc.append("customercode", Type.Str, "DUMMY")
        loc.append("companycode", Type.Str, "DUMMY")
        loc.append("latitude", Type.S32, 0)
        loc.append("longitude", Type.S32, 0)
        loc.append("accuracy", Type.U8, 0)
        root.children.append(loc)

        line = XMLNode("line")
        line.append("id", Type.Str, ".")
        line.append("class", Type.U8, 0)
        root.children.append(line)

        portfw = XMLNode("portfw")
        portfw.append("globalip", Type.IPv4_Int, ip_int)
        portfw.append("globalport", Type.U16, mech_data.get("global_port", 5730))
        portfw.append("privateport", Type.U16, mech_data.get("private_port", 5730))
        root.children.append(portfw)

        public = XMLNode("public")
        public.append("flag", Type.U8, 1)
        public.append("name", Type.Str, "." if not name else name)
        public.append("latitude", Type.Str, "0")
        public.append("longitude", Type.Str, "0")
        root.children.append(public)

        share = XMLNode("share")
        eacoin = XMLNode("eacoin")
        eacoin.append("notchamount", Type.S32, 3000)
        eacoin.append("notchcount", Type.S32, 3)
        eacoin.append("supplylimit", Type.S32, 10000)
        share.children.append(eacoin)

        eapass = XMLNode("eapass")
        eapass.append("valid", Type.U16, 365)
        share.children.append(eapass)

        url = XMLNode("url")
        url.append("eapass", Type.Str, "www.ea-pass.konami.net")
        url.append("arcadefan", Type.Str, "www.konami.jp/am")
        url.append("konaminetdx", Type.Str, "http://am.573.jp")
        url.append("konamiid", Type.Str, "https://id.konami.net")
        url.append("eagate", Type.Str, "http://eagate.573.jp")
        share.children.append(url)
        root.children.append(share)

        return root

    async def _get_card_by_konami_id(self, card_id: str):
        """Resolve a Konami E004 binding before falling back to the cabinet IDm."""
        card = await self.data.card.get_eamuse_card_by_access_code(card_id)
        if card is None:
            card = await self.data.card.get_eamuse_card_by_idm(card_id)
        return card

    async def handle_cardmng_inquire(self, request: XMLNode) -> XMLNode:
        card_id = request.xpath("@cardid/cardmng")
        card_type = request.xpath("@cardtype/cardmng")
        self.logger.info(f"Inquire access code for cardid {card_id} (type {card_type})")
        binded = "0"

        card = await self._get_card_by_konami_id(card_id)
        if card is None:
            self.logger.info(f"Cardid {card_id} (type {card_type}) does not exist")
            return XMLNode("cardmng", Type.Void, attributes={"status": "112"})

        if card["idm"] is None and card_id.upper().startswith("E004"):
            await self.data.card.set_eamuse_idm_by_card_id(card["id"], card_id)

        user = await self.data.user.get_user(card["user"])
        if card["pin"] is None:
            self.logger.info(f"Card {card_id} (type {card_type}) does not have pin set")
            return XMLNode("cardmng", Type.Void, attributes={"status": "112"})

        refid = await self.data.user.get_refid_by_user(
            card["user"], self.game, self.version, card["id"]
        )
        if refid is not None:
            binded = "1" if await self.check_profile(refid) else "0"
        
        else:
            last_game, last_version = self.get_previous_version()
            if last_game is not None and last_version is not None:
                oldref = await self.data.user.get_refid_by_user(card["user"], last_game, last_version)
                if oldref is not None:
                    binded = "1" if await self.check_succession_profile(oldref) else "0"
            
            refid = await self.data.user.create_refid(
                user["id"], self.game, self.version, card["id"]
            )

        attribs = dict(  # Order matters here for some reason
            binded=binded,
            dataid=refid,
            ecflag="1",
            expired="0",
            extidflag="1",
            newflag="0" if binded == "1" else "1",
            refid=refid,
            status="0",
            useridflag="1",
        )
        root = XMLNode.void("cardmng", **attribs)
        return root

    async def handle_cardmng_authpass(self, request: XMLNode) -> XMLNode:
        """
        Verify user PIN, return status 116 on fail. If we get to this point
        it's normally safe to assume the card has a password set but we should
        still verify that.
        """
        refid: str = request.xpath("@refid/cardmng")
        passwd: str = request.xpath("@pass/cardmng")
        userid = await self.data.user.get_user_id_by_refid(refid)

        if userid is None:
            self.logger.warning(f"Refid {refid} does not exist from {self.protocol.pcbid}")
            return XMLNode("cardmng", Type.Void, attributes={"status": "112"})

        rid_info = await self.data.user.get_refid_info_by_refid(refid)
        card = (
            await self.data.card.get_eamuse_card_by_id(rid_info["eamuse_card"])
            if rid_info["eamuse_card"] is not None
            else None
        )
        if card is None or card["pin"] is None:
            self.logger.warning(f"No card pin set for {refid} from {self.protocol.pcbid}")
            return XMLNode("cardmng", Type.Void, attributes={"status": "112"})

        if card["pin"] != passwd:
            self.logger.warning(f"Password fail for refid {refid} from {self.protocol.pcbid}")
            return XMLNode("cardmng", Type.Void, attributes={"status": "116"})

        self.logger.info(f"Refid {refid} successfull pin from {self.protocol.pcbid}")
        return XMLNode("cardmng")

    async def handle_cardmng_getrefid(self, request: XMLNode) -> XMLNode:
        cardid: str = request.xpath("@cardid/cardmng")
        card_type: str = request.xpath("@cardtype/cardmng")
        passwd: str = request.xpath("@passwd/cardmng")

        if len(passwd) != 4 or not passwd.isdigit():
            self.logger.error(
                f"handle_cardmng_getrefid: Invalid password {passwd} for card {cardid} (type {card_type})"
            )
            return XMLNode("cardmng", Type.Void, attributes={"status": "116"})

        card = await self._get_card_by_konami_id(cardid)
        if card is None:
            if not self.core_config.server.allow_user_registration:
                self.logger.error(f"Registration of card {cardid} (type {card_type}) blocked!")
                return XMLNode("cardmng", Type.Void, attributes={"status": "110"})

            userid = await self.data.arcade.get_machine_owner(self.protocol.pcbid)
            if userid is None:
                self.logger.error(
                    f"handle_cardmng_getrefid: No unique arcade owner for PCBID {self.protocol.pcbid}"
                )
                return XMLNode("cardmng", Type.Void, attributes={"status": "110"})

            user = await self.data.user.get_user(userid)
            if user is None:
                self.logger.error(
                    f"handle_cardmng_getrefid: Arcade owner {userid} does not exist"
                )
                return XMLNode("cardmng", Type.Void, attributes={"status": "110"})

            if card_type == "2": # type 2 cards could reasonably also be used on sega games
                kid = self.data.card.to_access_code(cardid)
            else:
                kid = uid_to_konami(cardid, self.data.config.eamuse.card_key.encode())
            
            card = await self.data.card.create_eamuse_card(userid, kid)
            if card is None:
                self.logger.error(
                    f"handle_cardmng_getrefid: Failed to create card for user {userid}!"
                )
                return XMLNode("cardmng", Type.Void, attributes={"status": "110"})

            await self.data.user.set_eamuse_card_pin(card, passwd)
            await self.data.card.set_eamuse_idm_by_card_id(card, cardid)
            card = await self.data.card.get_eamuse_card_by_id(card)

        else:
            user = await self.data.user.get_user(card["user"])  # User can't be none, SQL would throw a fit.
            userid = user["id"]
            if card["pin"] is not None and card["pin"] != passwd:
                self.logger.error(
                    f"handle_cardmng_getrefid: PIN mismatch for bound card {cardid}"
                )
                return XMLNode("cardmng", Type.Void, attributes={"status": "116"})

            if card["pin"] is None:
                await self.data.user.set_eamuse_card_pin(card["id"], passwd)

            if card["idm"] is None:
                await self.data.card.set_eamuse_idm_by_card_id(card["id"], cardid)

        refid = await self.data.user.create_refid(
            userid, self.game, self.version, card["id"]
        )
        if refid is None:
            self.logger.error(
                f"handle_cardmng_getrefid: Failed to create refid for user {user} game {self.game} version {self.version}!"
            )
            return XMLNode("cardmng", Type.Void, attributes={"status": "110"})

        return XMLNode("cardmng", Type.Void, attributes={"dataid": refid, "refid": refid})

    async def handle_cardmng_bindmodel(self, request: XMLNode) -> XMLNode:
        req_refid = request.xpath("@refid/cardmng")
        rid_info = await self.data.user.get_refid_info_by_refid(req_refid)

        if rid_info['game'] != self.game and rid_info['version'] != self.version:
            self.logger.warning(f"Game {self.game} v{self.version} requested refid bind that belongs to {rid_info['game']} v{rid_info['version']}")
        else:
            self.bind_profile(req_refid)
        
        return XMLNode("cardmng", Type.Void, attributes={"dataid": req_refid, "refid": req_refid})

    async def handle_cardmng_getkeepspan(self, request: XMLNode) -> XMLNode:
        return XMLNode("cardmng", Type.Void, attributes={"keepspan": "30"})

    async def handle_cardmng_getdatalist(self, request: XMLNode) -> XMLNode:
        return XMLNode("cardmng")

    async def handle_pcbevent_put(self, request: XMLNode) -> XMLNode:
        evt_items: List[XMLNode] = []
        for x in request.xpath("pcbevent"):
            if x.name == "item":
                evt_items.append(x)

        for item in evt_items:
            evt_name: XMLNode = item.xpath("name").value
            evt_value: XMLNode = item.xpath("value").value
            evt_name_readable = self.decode_pcbevent(evt_name, evt_value)
            self.logger.info(
                f"PCB Event: {self.protocol.model} | {self.protocol.pcbid} | {evt_name_readable}"
            )

            await self.data.base.log_event(
                "eamuse",
                "PCBEVENT",
                logging.INFO,
                evt_name_readable,
                {
                    "model": str(self.protocol.model),
                    "pcbid": self.protocol.pcbid,
                    "value": evt_value,
                    "evt_raw": evt_name,
                },
                ip=self.protocol.client_ip,
                game=self.protocol.model.gamecode,
                version=self.protocol.model.datecode
            )

        return XMLNode("pcbevent")

    async def handle_package_list(self, request: XMLNode) -> XMLNode:
        return XMLNode("package")

    async def handle_package_intend(self, request: XMLNode) -> XMLNode:
        return XMLNode("package")

    async def handle_eacoin_checkin(self, request: XMLNode) -> XMLNode:
        cardid = request.xpath('eacoin/cardid').value
        passwd = request.xpath('eacoin/passwd').value
        card = await self.data.card.get_eamuse_card_by_idm(cardid)
        if card is None and cardid.startswith("E004"):
            card = await self.data.card.get_eamuse_card_by_access_code(cardid)
        if card is not None:
            if card["idm"] is None and cardid.upper().startswith("E004"):
                await self.data.card.set_eamuse_idm_by_card_id(card["id"], cardid)
            access_code = card["access_code"]
            userid = int(card["user"])
        else:
            try:
                access_code = self.data.card.to_access_code(cardid)
            except ValueError:
                self.logger.warning(f"Invalid e-amusement card ID {cardid} from {self.protocol.pcbid}")
                return XMLNode("eacoin", Type.Void, attributes={"status": "112"})
            card = await self.data.card.get_eamuse_card_by_access_code(access_code)
            userid = int(card["user"]) if card is not None else None
        machine = await self.data.arcade.get_bemani_machine(self.protocol.pcbid)

        if userid is None:
            self.logger.warning(f"Card {access_code} not registered from {self.protocol.pcbid}")
            return XMLNode("eacoin", Type.Void, attributes={"status": "112"})

        if card is None or card["pin"] is None:
            self.logger.warning(f"No card pin set for card {access_code} from {self.protocol.pcbid}")
            return XMLNode("eacoin", Type.Void, attributes={"status": "109"})

        if card["pin"] != passwd:
            self.logger.warning(f"Password fail for access code {access_code} from {self.protocol.pcbid}")
            return XMLNode("eacoin", Type.Void, attributes={"status": "116"})

        if not machine:
            self.logger.error(f"Unregistered machine {self.protocol.pcbid} attempted paseli checkin!")
            return XMLNode("eacoin", Type.Void, attributes={"status": "110"}) # TODO: Different fault

        self.logger.info(f"Paseli checkin for user {userid}")
        eacoin = XMLNode.void("eacoin")

        old_seshes = await self.data.user.get_open_paseli_sessions_by_user(userid)
        if old_seshes:
            pass # TODO: Handle hanging sessions
    
        bal = INFINITE_PASELI_BALANCE
        if not self.core_config.eamuse.global_infinite_paseli:
            balance_arcade = (
                machine["arcade"]
                if not self.core_config.eamuse.global_paseli_balances
                else None
            )
            wallet = await self.data.user.get_paseli_balance_by_user_arcade(
                userid, balance_arcade
            )
            if wallet is None:
                bal = 0
                await self.data.user.create_paseli_balance(userid, balance_arcade)
            elif not wallet["is_infinite"]:
                bal = wallet["balance"]
        
        sesh = await self.data.user.create_paseli_session(userid, machine['id'], self.protocol.model.gamecode)
        if not sesh:
            self.logger.error(f"Failed to start paseli session for user {userid} at machine {self.protocol.pcbid} running {self.protocol.model}")
            return XMLNode("eacoin", Type.Void, attributes={"status": "116"}) # TODO: Different fault
        
        eacoin.append("balance", Type.S32, bal)
        eacoin.append("sessid", Type.Str, sesh)
        eacoin.append("acstatus", Type.U8, 0)
        eacoin.append("sequence", Type.S16, 0)
        eacoin.append("acid", Type.Str, "PASELI_AC_ID") # TODO: un-dummy these when I figure out what they're for
        eacoin.append("acname", Type.Str, "PASELI_AC_NAME")
        eacoin.append("inshopcharge", Type.U8, 0) # ?
        return eacoin

    async def handle_eacoin_consume(self, request: XMLNode) -> XMLNode:
        sesh = request.xpath('eacoin/sessid').value
        seq = request.xpath('eacoin/sequence').value
        ammount = request.xpath('eacoin/payment').value
        detail = request.xpath('eacoin/detail').value

        eacoin = XMLNode.void("eacoin")
        eacoin.append("autocharge", Type.U8, 0)

        session = await self.data.user.get_paseli_session_by_id(sesh)
        if not session:
            self.logger.error(f"Paseli session {sesh} sent by {self.protocol.pcbid} does not exist!")
            eacoin.append("acstatus", Type.U8, 1)
            eacoin.append("balance", Type.S32, 0)
            return eacoin
        
        if session['closed']:
            self.logger.error(f"{self.protocol.pcbid} attempted to add transaction to closed Paseli session {sesh}!")
            eacoin.append("acstatus", Type.U8, 1)
            eacoin.append("balance", Type.S32, 0)
            return eacoin

        if session['opened'].timestamp() < datetime.now().timestamp() - 86400: # More then 24h old
            self.logger.error(f"{self.protocol.pcbid} attempted to add transaction to stale Paseli session {sesh}!")
            await self.data.user.close_paseli_session(sesh)
            eacoin.append("acstatus", Type.U8, 1)
            eacoin.append("balance", Type.S32, 0)
            return eacoin
        
        self.logger.info(f"Paseli session {sesh} (user {session['user']} machine {session['machine']}) paid {ammount}p for {self.decode_paseli_item(detail)} at machine {self.protocol.pcbid} (tx #{seq})")
        
        machine = await self.data.arcade.get_machine(id=session["machine"])
        balance = INFINITE_PASELI_BALANCE - ammount
        acstatus = 0
        charged = True

        if not self.core_config.eamuse.global_infinite_paseli:
            balance = 0
            acstatus = 1
            charged = False
            balance_arcade = (
                None
                if self.core_config.eamuse.global_paseli_balances
                else machine["arcade"]
            )
            wallet = await self.data.user.get_paseli_balance_by_user_arcade(
                session["user"], balance_arcade
            )
            if wallet is not None:
                if wallet["is_infinite"]:
                    balance = INFINITE_PASELI_BALANCE - ammount
                    acstatus = 0
                    charged = True
                elif wallet["balance"] < ammount:
                    self.logger.error(
                        f"{self.protocol.pcbid} attempted to charge {ammount} paseli "
                        f"from {session['user']} but balance was insufficient!"
                    )
                    balance = wallet["balance"]
                else:
                    await self.data.user.spend_paseli_balance_by_id(
                        wallet["id"], ammount
                    )
                    balance = wallet["balance"] - ammount
                    acstatus = 0
                    charged = True

        if charged:
            await self.data.user.put_paseli_transaction(
                session["id"], seq, -ammount, detail, self.decode_paseli_item(detail)
            )
        eacoin.append("acstatus", Type.U8, acstatus)
        eacoin.append("balance", Type.S32, balance)
        return eacoin

    async def handle_eacoin_opcheckin(self, request: XMLNode) -> XMLNode:
        eacoin = XMLNode("eacoin")
        eacoin.append("sessid", Type.Str, f"OPCK-{self.protocol.pcbid}-{int(datetime.now().timestamp())}")
        return eacoin

    async def handle_eacoin_getlog(self, request: XMLNode) -> XMLNode:
        # one of last7days, last52weeks, eachday, eachhour, and lastmonths for ops, and detail for users
        logtype = request.xpath("eacoin/logtype").value
        root = XMLNode("eacoin")
        topic = XMLNode(logtype)
        topic.append("sumdate", Type.Str, datetime.now().strftime("%Y-%m-%d"))
        topic.append("sumfrom", Type.Str, "2024-04-07 19:00:00")
        topic.append("sumto", Type.Str, "2024-04-14 19:00:00")

        root.children.append(topic)
        root.children.append(XMLNode("processing", Type.U8, 0))
        return root

    async def handle_eacoin_checkout(self, request: XMLNode) -> XMLNode:
        sesh = request.xpath('eacoin/sessid').value
        await self.data.user.close_paseli_session(sesh)
        return XMLNode("eacoin")

    async def handle_eacoin_opcheckout(self, request: XMLNode) -> XMLNode:
        return XMLNode("eacoin")

    async def handle_eacoin_opchpass(self, request: XMLNode) -> XMLNode:
        pass

    async def handle_message_get(self, request: XMLNode) -> XMLNode:
        return XMLNode.void("message")

    async def handle_dlstatus_progress(self, request: XMLNode) -> XMLNode:
        prog = request.xpath("dlstatus/progress").value
        self.logger.info(f"{self.protocol.pcbid}'s update of {self.protocol.model.gamecode} is {prog}% complete")
        return XMLNode("dlstatus")

    async def handle_dlstatus_done(self, request: XMLNode) -> XMLNode:
        name = request.xpath("dlstatus/name").value
        self.logger.info(f"{self.protocol.pcbid}'s update of {name} is complete")

        root = XMLNode("dlstatus")
        root.append("progress", Type.S32, 1)
        return root

class EamuseServlet:
    dispatchers: Dict[str, BaseDispatcher] = {}
    def __init__(self, cfg: CoreConfig, cfg_dir: str) -> None:
        self.config = cfg
        self.config_dir = cfg_dir
        self.data = Data(cfg)

        self.logger = logging.getLogger("eamuse")
        log_fmt_str = "[%(asctime)s] Eamuse | %(levelname)s | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)

        fileHandler = TimedRotatingFileHandler(
            "{0}/{1}.log".format(self.config.server.log_dir, "eamuse"),
            when="d",
            backupCount=10,
        )
        fileHandler.setFormatter(log_fmt)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(log_fmt)

        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)

        self.logger.setLevel(cfg.eamuse.loglevel)
        coloredlogs.install(level=cfg.eamuse.loglevel, logger=self.logger, fmt=log_fmt_str)

        for _, mod in Utils.get_all_titles().items():
            if hasattr(mod, "is_eamuse") and mod.is_eamuse == True:
                if hasattr(mod, "index") and hasattr(mod, "game_codes"):
                    for code in mod.game_codes:
                        if mod.index.is_game_enabled(code, cfg, cfg_dir):
                            self.dispatchers[code] = mod.index(cfg, cfg_dir)

        self.logger.info(f"Serving {len(self.dispatchers)} game IDs")
    
    async def handle_eareq_slash(self, request: Request) -> Response:
        body = await request.body()
        method = f"{request.path_params.get('module', '')}.{request.path_params.get('method', '')}"
        return await self.handle_eareq(
            request.path_params.get("model", ""),
            method,
            request.headers,
            body,
            Utils.get_ip_addr(request)
        )

    async def handle_eareq_query(self, request: Request) -> Response:
        if "f" in request.query_params:
            method = request.query_params.get("f", "")
        elif "module" in request.query_params and "method" in request.query_params:
            method = f"{request.query_params.get('module', '')}.{request.query_params.get('method', '')}"
        else:
            method=""
        
        body = await request.body()
        return await self.handle_eareq(
            request.query_params.get("model", ""),
            method,
            request.headers,
            body,
            Utils.get_ip_addr(request)
        )

    async def handle_eareq(self, model: str, method: str, headers: Dict, data: bytes, client_ip: str = "0.0.0.0") -> Response:

        self.logger.log(5, f"{model} {method} from {client_ip}: {headers} | {data.hex()}")
        module = method.split(".")[0]
        eainfo = headers.get("x-eamuse-info", None)
        
        try:
            proto = EAProtocol(
                data,
                headers.get("x-compress", None),
                eainfo,
                bytes.fromhex(self.config.eamuse.shared_secret),
                model,
                method,
                client_ip
            )
        except Exception as e:
            self.logger.error(f"Failed to parse {model} - {method} request: {e}")
            tp, val, tb  = sys.exc_info()
            traceback.print_exception(tp, val, tb, limit=10)
            with open("{0}/{1}.log".format(self.config.server.log_dir, "eamuse"), "a") as f:
                traceback.print_exception(tp, val, tb, limit=10, file=f)
            return self.gen_fault_resp(module, FAULT_MALFORMED_REQUEST, eainfo)
        
        if not self.config.server.allow_unregistered_serials:
            cab = await self.data.arcade.get_bemani_machine(proto.pcbid)
            if cab is None:
                self.logger.warning(f"Unknown PCBID {proto.pcbid} running {proto.model} tried to access {proto.method}")
                return self.gen_fault_resp(module, FAULT_EA_REGISTRATION_NEEDED, eainfo)

        dispatcher = self.dispatchers.get(proto.model.gamecode, None)
        if not dispatcher:
            self.logger.warning(f"Unsupported game {proto.model.gamecode}")
            return self.gen_fault_resp(module, FAULT_GAME_UNSUPORTED, eainfo)
        
        internal_ver = dispatcher.get_game_version(proto)
        if internal_ver == -1: # datecode too old
            self.logger.error(f"{proto.model.gamecode} does not dispatch {proto.model.datecode} (too old)")
            return self.gen_fault_resp(module, FAULT_GAME_OLD, eainfo)
        
        elif internal_ver == -2: # datecode too new
            self.logger.error(f"{proto.model.gamecode} does not dispatch {proto.model.datecode} (too new)")
            return self.gen_fault_resp(module, FAULT_GAME_UNSUPORTED, eainfo)
        
        try:
            resp = await dispatcher.dispatch(proto, internal_ver)
            if resp is None:
                self.logger.warning(f"{proto.model.gamecode} returned no data for {proto.method}")
                return self.gen_empty_resp(module, eainfo)
        
        except Exception as e:
            self.logger.error(f"Error with {proto.model.gamecode} dispatching {proto.method} - {e}")
            tp, val, tb  = sys.exc_info()
            traceback.print_exception(tp, val, tb, limit=4)
            with open("{0}/{1}.log".format(self.config.server.log_dir, "eamuse"), "a") as f:
                traceback.print_exception(tp, val, tb, limit=4, file=f)
            
            return self.gen_fault_resp(module, FAULT_BAD_GAME, eainfo)
        
        if resp.name != "response":
            if "status" not in resp.attributes:
                resp.attributes['status'] = "0"
            
            response_attributes = (
                {"dstid": proto.pcbid} if proto.pcbid is not None else None
            )
            resp_root = XMLNode(
                "response", Type.Void, attributes=response_attributes
            )
            resp_root.children.append(resp)
            proto.set_resp(resp_root)
            return self.gen_resp(proto.get_resp_packet(), eainfo)
        
        else:
            if proto.pcbid is not None and "dstid" not in resp.attributes:
                resp.attributes["dstid"] = proto.pcbid
            proto.set_resp(resp)
            return self.gen_resp(proto.get_resp_packet(), eainfo) 
    
    def gen_resp(self, packet: bytes, eainfo: str) -> Response:
        resp = Response(packet)
        resp.headers['x-compress'] = "none"
        if eainfo:
            resp.headers['x-eamuse-info'] = eainfo

        return resp

    def gen_fault_resp(self, module: str, fault: str, ea_info: str) -> Response:
        root = XMLNode.void("response", fault=fault)
        root.children.append(XMLNode.void(module))
        enc = Encoder().encode(root)
        if ea_info is not None:
            data = ea_symmetric_crypt(
                enc, ea_info, bytes.fromhex(self.config.eamuse.shared_secret),
            )
        else:
            data = enc
        
        return self.gen_resp(data, ea_info)

    def gen_empty_resp(self, module: str, ea_info: str) -> Response:
        root = XMLNode.void("response")
        root.children.append(XMLNode.void(module))
        enc = Encoder().encode(root)
        if ea_info is not None:
            data = ea_symmetric_crypt(
                enc, ea_info, bytes.fromhex(self.config.eamuse.shared_secret),
            )
        
        else:
            data = enc
        
        return self.gen_resp(data, ea_info)
