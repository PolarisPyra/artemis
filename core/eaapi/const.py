import enum

from dataclasses import dataclass
from html import unescape
from typing import List, Callable

from .misc import assert_true


CARD_ALPHABET = "0123456789ABCDEFGHJKLMNPRSTUWXYZ"

NAME_MAX_COMPRESSED = 0x24
NAME_MAX_DECOMPRESSED = 0x1000

ENCODING = {
    0x20: "ascii",
    0x40: "iso-8859-1",
    0x60: "euc-jp",
    0x80: "shift-jis",
    0xA0: "utf-8",
}
DEFAULT_ENCODING = ENCODING[0x80]  # Shift-JIS
ENCODING[0x00] = DEFAULT_ENCODING
XML_ENCODING = {
    "ASCII": "ascii",
    "ISO-8859-1": "iso-8859-1",
    "EUC-JP": "euc-jp",
    "SHIFT_JIS": "shift-jis",
    "SHIFT-JIS": "shift-jis",
    "UTF-8": "utf-8",
}
ENCODING_BACK = {v: k for k, v in ENCODING.items()}
XML_ENCODING_BACK = {v: k for k, v in XML_ENCODING.items()}
XML_ENCODING_BACK["shift-jis"] = "SHIFT_JIS"
ATTR = 0x2E
END_NODE = 0xFE
END_DOC = 0xFF
PACK_ALPHABET = "0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"

CONTENT_COMP_FULL = 0x42
CONTENT_COMP_SCHEMA = 0x43
CONTENT_FINGERPRINT = 0x44  # TODO: Identify how exactly this differs from the others
CONTENT_ASCII_FULL = 0x45
CONTENT_ASCII_SCHEMA = 0x46

CONTENT_COMP = (CONTENT_COMP_FULL, CONTENT_COMP_SCHEMA)
CONTENT_FULL = (CONTENT_COMP_FULL, CONTENT_ASCII_FULL)
CONTENT = (
    CONTENT_COMP_FULL, CONTENT_COMP_SCHEMA, CONTENT_FINGERPRINT,
    CONTENT_ASCII_FULL, CONTENT_ASCII_SCHEMA
)

ARRAY_BIT = 0x40
ARRAY_MASK = ARRAY_BIT - 1

FAULT_BAD_PCBID = "0100"
FAULT_BAD_ARCADE = "0101"
FAULT_BAD_GAME = "0102"
FAULT_OUT_OF_SERVICE = "0117"
FAULT_EA_ENDED = "0121"
FAULT_MALFORMED_REQUEST = "0125"
FAULT_EA_REGISTRATION_NEEDED = "0127"
FAULT_MAINTENANCE = "0128"
FAULT_GAME_OLD = "0133"
FAULT_GAME_UNSUPORTED = "0138"


@dataclass
class _Type:
    id: int
    fmt: str
    names: List[str]
    c_name: str
    convert: Callable | None
    size: int = 1
    no_check: bool = False

    def _parse(self, value):
        if self.convert is None:
            return ()
        if self.size == 1:
            if isinstance(value, (list, tuple)) and len(value) == 1:
                value = value[0]
            return self.convert(value)
        if not self.no_check:
            assert_true(len(value) == self.size, "Invalid node data")
        return (*map(self.convert, value),)


def parse_ip(ip: int | str) -> tuple[int, int, int, int]:
    if isinstance(ip, int):
        return (
            (ip >> 24) & 0xff,
            (ip >> 16) & 0xff,
            (ip >> 8) & 0xff,
            (ip >> 0) & 0xff,
        )
    return (*map(int, ip.split(".")),)


class Type(enum.Enum):
    Void = _Type(0x01, "", ["void"], "void", None)
    S8 = _Type(0x02, "b", ["s8"], "int8", int)
    U8 = _Type(0x03, "B", ["u8"], "uint8", int)
    S16 = _Type(0x04, "h", ["s16"], "int16", int)
    U16 = _Type(0x05, "H", ["u16"], "uint16", int)
    S32 = _Type(0x06, "i", ["s32"], "int32", int)
    U32 = _Type(0x07, "I", ["u32"], "uint32", int)
    S64 = _Type(0x08, "q", ["s64"], "int64", int)
    U64 = _Type(0x09, "Q", ["u64"], "uint64", int)
    Blob = _Type(0x0a, "S", ["bin", "binary"], "char[]", bytes)
    Str = _Type(0x0b, "s", ["str", "string"], "char[]", unescape)
    IPv4 = _Type(0x0c, "4B", ["ip4"], "uint8[4]", parse_ip, 1, True)
    IPv4_Int = _Type(0x0c, "I", ["ip4"], "uint8[4]", parse_ip, 1, True)
    Time = _Type(0x0d, "I", ["time"], "uint32", int)
    Float = _Type(0x0e, "f", ["float", "f"], "float", float)
    Double = _Type(0x0f, "d", ["double", "d"], "double", float)

    TwoS8 = _Type(0x10, "2b", ["2s8"], "int8[2]", int, 2)
    TwoU8 = _Type(0x11, "2B", ["2u8"], "uint8[2]", int, 2)
    TwoS16 = _Type(0x12, "2h", ["2s16"], "int16[2]", int, 2)
    TwoU16 = _Type(0x13, "2H", ["2u16"], "uint16[2]", int, 2)
    TwoS32 = _Type(0x14, "2i", ["2s32"], "int32[2]", int, 2)
    TwoU32 = _Type(0x15, "2I", ["2u32"], "uint32[2]", int, 2)
    TwoS64 = _Type(0x16, "2q", ["2s64", "vs64"], "int16[2]", int, 2)
    TwoU64 = _Type(0x17, "2Q", ["2u64", "vu64"], "uint16[2]", int, 2)
    TwoFloat = _Type(0x18, "2f", ["2f"], "float[2]", float, 2)
    TwoDouble = _Type(0x19, "2d", ["2d", "vd"], "double[2]", float, 2)

    ThreeS8 = _Type(0x1a, "3b", ["3s8"], "int8[3]", int, 3)
    ThreeU8 = _Type(0x1b, "3B", ["3u8"], "uint8[3]", int, 3)
    ThreeS16 = _Type(0x1c, "3h", ["3s16"], "int16[3]", int, 3)
    ThreeU16 = _Type(0x1d, "3H", ["3u16"], "uint16[3]", int, 3)
    ThreeS32 = _Type(0x1e, "3i", ["3s32"], "int32[3]", int, 3)
    ThreeU32 = _Type(0x1f, "3I", ["3u32"], "uint32[3]", int, 3)
    ThreeS64 = _Type(0x20, "3q", ["3s64"], "int64[3]", int, 3)
    ThreeU64 = _Type(0x21, "3Q", ["3u64"], "uint64[3]", int, 3)
    ThreeFloat = _Type(0x22, "3f", ["3f"], "float[3]", float, 3)
    ThreeDouble = _Type(0x23, "3d", ["3d"], "double[3]", float, 3)

    FourS8 = _Type(0x24, "4b", ["4s8"], "int8[4]", int, 4)
    FourU8 = _Type(0x25, "4B", ["4u8"], "uint8[4]", int, 4)
    FourS16 = _Type(0x26, "4h", ["4s16"], "int16[4]", int, 4)
    FourU16 = _Type(0x27, "4H", ["4u16"], "uint8[4]", int, 4)
    FourS32 = _Type(0x28, "4i", ["4s32", "vs32"], "int32[4]", int, 4)
    FourU32 = _Type(0x29, "4I", ["4u32", "vs32"], "uint32[4]", int, 4)
    FourS64 = _Type(0x2a, "4q", ["4s64"], "int64[4]", int, 4)
    FourU64 = _Type(0x2b, "4Q", ["4u64"], "uint64[4]", int, 4)
    FourFloat = _Type(0x2c, "4f", ["4f", "vf"], "float[4]", float, 4)
    FourDouble = _Type(0x2d, "4d", ["4d"], "double[4]", float, 4)

    Attr = _Type(0x2e, "s", ["attr"], "char[]", None)
    Array = _Type(0x2f, "", ["array"], "", None)

    VecS8 = _Type(0x30, "16b", ["vs8"], "int8[16]", int, 16)
    VecU8 = _Type(0x31, "16B", ["vu8"], "uint8[16]", int, 16)
    VecS16 = _Type(0x32, "8h", ["vs16"], "int8[8]", int, 8)
    VecU16 = _Type(0x33, "8H", ["vu16"], "uint8[8]", int, 8)

    Bool = _Type(0x34, "b", ["bool", "b"], "bool", int)
    TwoBool = _Type(0x35, "2b", ["2b"], "bool[2]", int, 2)
    ThreeBool = _Type(0x36, "3b", ["3b"], "bool[3]", int, 3)
    FourBool = _Type(0x37, "4b", ["4b"], "bool[4]", int, 4)
    VecBool = _Type(0x38, "16b", ["vb"], "bool[16]", int, 16)

    @classmethod
    def from_val(cls, value):
        for i in cls:
            if i.value.id == value & ARRAY_MASK:
                return i
        raise ValueError(f"Unknown node type {value}")


class ServicesMode(enum.Enum):
    Operation = "operation"
    Debug = "debug"
    Test = "test"
    Factory = "factory"


class Compression(enum.Enum):
    Lz77 = "lz77"
    None_ = "none"
