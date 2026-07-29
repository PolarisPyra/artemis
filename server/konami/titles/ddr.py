"""Native DDR e-amusement handlers."""

from __future__ import annotations

import base64
import hashlib
from typing import ClassVar

from server.konami.protocol import EamuseInfo, EamuseResponse
from server.konami.router import EamuseRouter
from server.sega.config import ArtemisConfig
from server.sega.data import Data

from .popn_support.helpers import attr, content, item


class DDRRoutes:
    """Port the shared DDR X/A playerdata protocol."""

    # MDX is the modern plugin code; HDX is the older bemanitools DDR code.
    game_codes: ClassVar[tuple[str, ...]] = ("MDX", "HDX")

    @classmethod
    def service_modules(cls, game_code: str, model: str = "") -> tuple[str, ...]:
        return ("playerdata", "system", "eventlog")

    def __init__(self, cfg: ArtemisConfig) -> None:
        self.data = Data(cfg)

    def register(self, router: EamuseRouter) -> None:
        routes = {
            "playerdata": {
                "usergamedata_advanced": self.usergamedata,
                "usergamedata_recv": self.usergamedata_recv,
                "usergamedata_send": self.usergamedata_send,
            },
            "system": {"convcardnumber": self.convcardnumber},
            "eventlog": {"write": self.eventlog_write},
        }
        for code in self.game_codes:
            for module, methods in routes.items():
                for method, handler in methods.items():
                    router.add(code, module, method, handler)

    async def usergamedata(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        mode = content(payload.get("mode")) or attr(payload, "mode", "")
        refid = content(payload.get("refid")) or attr(payload, "refid", "")
        if mode == "usernew":
            await self._new_profile(refid, content(payload.get("shoparea")) or "")
            response.content = {
                "result": item("s32", 0),
                "seq": item("str", self._seq(refid)),
                "code": item("s32", self._id(refid)),
                "shoparea": item("str", content(payload.get("shoparea")) or ""),
            }
            return
        if mode == "userload":
            response.content = await self._load(refid)
            return
        if mode == "usersave":
            await self._save(refid, payload)
            response.content = {"result": item("s32", 0)}
            return
        if mode == "rivalload":
            response.content = {"result": item("s32", 0), "data": {"recordtype": item("s32", _number(payload.get("loadflag"))), "record": []}}
            return
        if mode == "ghostload":
            response.content = {"result": item("s32", 0), "ghostdata": {}}
            return
        if mode == "inheritance":
            response.content = {"result": item("s32", 0)}
            return
        response.status = 110

    async def usergamedata_recv(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = content(payload.get("refid")) or attr(payload, "refid", "")
        profile = await self.data.konami.get_profile(refid)
        requested = str(content(payload.get("recv_csv")) or "")
        types = [value for index, value in enumerate(requested.split(",")) if index % 2 == 0 and value]
        records = []
        for record_type in types:
            stored = (profile or {}).get("usergamedata", {}).get(record_type, {})
            string_data = stored.get("strdata", "<NODATA>")
            binary_data = stored.get("bindata", "")
            node = {"@content": base64.b64encode(str(string_data).encode()).decode()}
            if binary_data:
                node["bin1"] = item("str", base64.b64encode(_bytes(binary_data)).decode())
            records.append(node)
        response.content = {
            "result": item("s32", 0),
            "player": {"record": [{"d": records}], "record_num": item("u32", len(records))},
        }

    async def usergamedata_send(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        refid = content(payload.get("refid")) or attr(payload, "refid", "")
        profile = await self.data.konami.get_profile(refid)
        if profile is None:
            response.status = 109
            return
        records = profile.setdefault("usergamedata", {})
        for node in _nodes(_nested(payload, "record.d")):
            encoded = content(node, "") if isinstance(node, dict) else node
            try:
                decoded = base64.b64decode(str(encoded)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                continue
            fields = decoded.split(",")
            if len(fields) < 2:
                continue
            record_type = fields[1]
            binary = content(node.get("bin1"), "") if isinstance(node, dict) else ""
            records[record_type] = {
                "strdata": ",".join(fields[2:-1]),
                "bindata": binary,
            }
        await self.data.konami.put_profile(refid, profile)
        response.content = {"result": item("s32", 0)}

    async def convcardnumber(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        payload = data.get("data", data)
        card_id = content(payload.get("card_id")) or ""
        response.content = {
            "result": item("s32", 0),
            "data": {"card_number": item("str", str(card_id).split("|", 1)[0])},
        }

    async def eventlog_write(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.content = {
            "gamesession": item("s64", 1),
            "logsendflg": item("s32", 0),
            "logerrlevel": item("s32", 0),
            "evtidnosendflg": item("s32", 0),
        }

    async def success(
        self, info: EamuseInfo, data: dict, response: EamuseResponse
    ) -> None:
        response.status = 0

    async def _new_profile(self, refid: str, shoparea: str) -> None:
        if not refid or await self.data.konami.get_profile(refid) is not None:
            return
        await self.data.konami.put_profile(
            refid,
            {
                "collection": "profile",
                "ddrCode": self._id(refid),
                "shopArea": shoparea,
                "usergamedata": {},
            },
        )

    async def _load(self, refid: str) -> dict:
        profile = await self.data.konami.get_profile(refid)
        result = {
            "result": item("s32", 0),
            "is_new": item("bool", profile is None),
            "music": [],
            "eventdata": [],
        }
        if profile is None:
            return result
        scores = await self.data.konami.get_document(refid, "DDR", "score") or {}
        for score in scores.get("scores", []):
            notes = [
                {
                    "count": item("u16", 1),
                    "rank": item("u8", score.get("rank", 0)),
                    "clearkind": item("u8", score.get("clearKind", 0)),
                    "score": item("s32", score.get("score", 0)),
                    "ghostid": item("s32", score.get("songId", 0)),
                }
            ]
            notes.extend(
                {
                    "count": item("u16", 0),
                    "rank": item("u8", 0),
                    "clearkind": item("u8", 0),
                    "score": item("s32", 0),
                    "ghostid": item("s32", 0),
                }
                for _ in range(8)
            )
            result["music"].append(
                {"mcode": item("u32", score.get("songId", 0)), "note": notes}
            )
        result["grade"] = {
            "single_grade": item("u32", profile.get("singleGrade", 0)),
            "dougle_grade": item("u32", profile.get("doubleGrade", 0)),
        }
        return result

    async def _save(self, refid: str, payload: dict) -> None:
        if not refid:
            return
        await self._new_profile(refid, "")
        document = await self.data.konami.get_document(refid, "DDR", "score") or {
            "collection": "score",
            "scores": [],
        }
        notes = _nodes(payload.get("note"))
        for note in notes:
            song_id = _number(note.get("mcode"))
            entry = {
                "songId": song_id,
                "difficulty": _number(note.get("notetype")),
                "rank": _number(note.get("rank")),
                "clearKind": _number(note.get("clearkind")),
                "score": _number(note.get("score")),
            }
            existing = next((value for value in document["scores"] if value.get("songId") == song_id and value.get("difficulty") == entry["difficulty"]), None)
            if existing is None:
                document["scores"].append(entry)
            else:
                existing.update(entry)
        await self.data.konami.put_document(refid, "DDR", "score", document)

    async def _profile_for_refid(self, refid: str):
        return await self.data.konami.get_profile(refid)

    async def _new_profile_if_missing(self, refid: str):
        await self._new_profile(refid, "")

    def _id(self, refid: str) -> int:
        return int(hashlib.sha256(f"ddr:{refid}".encode()).hexdigest()[:8], 16) % 90_000_000 + 10_000_000

    def _seq(self, refid: str) -> str:
        value = f"{self._id(refid):08d}"
        return f"{value[:4]}-{value[4:]}"


def _number(value, default=0):
    if isinstance(value, dict):
        value = value.get("@content", default)
    if isinstance(value, list):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _nodes(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _nested(node, path):
    current = node
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _bytes(value):
    if isinstance(value, bytes):
        return value
    try:
        return base64.b64decode(value)
    except (ValueError, TypeError):
        return str(value).encode()
