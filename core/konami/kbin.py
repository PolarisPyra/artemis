"""K-bin codec compatible with Asphyxia CORE's KBinJSON format.

The codec keeps the same object convention as the XML adapter: ``@attr`` for
attributes and ``@content`` for typed payloads.
"""

from __future__ import annotations

import struct

SIGNATURE = 0xA0
CHARMAP = "0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
ENCODINGS = {0x00: "shift_jis", 0x20: "ascii", 0x40: "iso-8859-1", 0x60: "euc_jp", 0x80: "shift_jis", 0xA0: "utf-8"}
ENCODING_VALUES = {value: key for key, value in ENCODINGS.items()}
TYPES = {"void": 1, "bin": 10, "str": 11, "attr": 46, "nodeEnd": 190, "endSection": 191}
NUMBER_TYPES = {
    "s8": (2, "b", 1), "u8": (3, "B", 1), "s16": (4, "h", 2), "u16": (5, "H", 2),
    "s32": (6, "i", 4), "u32": (7, "I", 4), "s64": (8, "q", 8), "u64": (9, "Q", 8),
    "float": (14, "f", 4), "double": (15, "d", 8), "bool": (52, "B", 1),
    "ip4": (12, "I", 4), "time": (13, "I", 4),
}
TYPES.update({key: value[0] for key, value in NUMBER_TYPES.items()})


def is_kbin(data: bytes) -> bool:
    return len(data) >= 2 and data[0] == SIGNATURE and data[1] in (0x42, 0x45)


def _pack_name(name: str, compressed: bool, encoding: str) -> bytes:
    if compressed:
        bits = 0
        count = 0
        output = bytearray([len(name)])
        for char in name:
            bits = (bits << 6) | CHARMAP.index(char)
            count += 6
            if count >= 8:
                count -= 8
                output.append((bits >> count) & 0xFF)
                bits &= (1 << count) - 1
        if count:
            output.append((bits << (8 - count)) & 0xFF)
        return bytes(output)
    raw = name.encode(encoding, errors="replace")
    return bytes([(len(raw) - 1) | 0x40]) + raw


def _unpack_name(data: bytes, cursor: int, compressed: bool, encoding: str) -> tuple[str, int]:
    length = data[cursor]
    cursor += 1
    if not compressed:
        raw = data[cursor:cursor + length + 1]
        return raw.decode(encoding, errors="replace"), cursor + length + 1
    value = 0
    bits = 0
    result = []
    for _ in range(length):
        while bits < 6:
            value = (value << 8) | data[cursor]
            cursor += 1
            bits += 8
        bits -= 6
        result.append(CHARMAP[(value >> bits) & 0x3F])
        value &= (1 << bits) - 1 if bits else 0
    return "".join(result), cursor


def _align(cursor: int) -> int:
    return (cursor + 3) & ~3


def _read_stream(data: bytes, cursor: int, base: int = 0) -> tuple[bytes, int]:
    length = struct.unpack_from(">I", data, cursor)[0]
    cursor += 4
    result = data[cursor:cursor + length]
    return result, base + _align((cursor + length) - base)


def _read_value(data: bytes, cursor: int, fmt: str, count: int = 1, array: bool = False, base: int = 0):
    if array:
        size = struct.unpack_from(">I", data, cursor)[0]
        cursor += 4
        raw = data[cursor:cursor + size]
        cursor = base + _align((cursor + size) - base)
    else:
        size = struct.calcsize(">" + fmt) * count
        raw = data[cursor:cursor + size]
        cursor = base + _align((cursor + size) - base)
    item_size = struct.calcsize(">" + fmt)
    values = [struct.unpack_from(">" + fmt, raw, index)[0] for index in range(0, len(raw), item_size)]
    return values, cursor


def decode(data: bytes) -> tuple[dict, str]:
    if not is_kbin(data):
        raise ValueError("not a K-bin payload")
    compressed = data[1] == 0x42
    encoding = ENCODINGS.get(data[2], "utf-8")
    if data[3] != (0xFF ^ data[2]):
        raise ValueError("invalid K-bin encoding marker")
    node_length = struct.unpack_from(">I", data, 4)[0]
    node_start = 8
    node_end = node_start + node_length
    data_cursor = node_end + 4
    data_start = data_cursor
    node_cursor = node_start
    root: dict = {}
    current = root
    stack: list[dict] = []
    while node_cursor < node_end:
        token = data[node_cursor]
        node_cursor += 1
        is_array = bool(token & 0x40)
        token &= ~0x40
        if token == 0:
            continue
        if token == 191:
            break
        if token == 190:
            current = stack.pop() if stack else root
            continue
        name, node_cursor = _unpack_name(data, node_cursor, compressed, encoding)
        if token == 46:
            value, data_cursor = _read_stream(data, data_cursor, data_start)
            current.setdefault("@attr", {})[name] = value.rstrip(b"\0").decode(encoding, errors="replace")
            continue
        node: dict = {}
        parent = current
        if name in parent:
            if not isinstance(parent[name], list):
                parent[name] = [parent[name]]
            parent[name].append(node)
        else:
            parent[name] = node
        stack.append(parent)
        current = node
        type_name = next((key for key, value in TYPES.items() if value == token), "void")
        current["@attr"] = {"__type": type_name}
        if token == 1:
            continue
        if type_name == "str":
            value, data_cursor = _read_stream(data, data_cursor)
            current["@content"] = value.rstrip(b"\0").decode(encoding, errors="replace")
        elif type_name == "bin":
            current["@content"], data_cursor = _read_stream(data, data_cursor, data_start)
        else:
            fmt = NUMBER_TYPES[type_name][1]
            current["@content"], data_cursor = _read_value(data, data_cursor, fmt, 1, is_array, data_start)
            if is_array:
                current["@attr"]["__count"] = len(current["@content"])
    return root, encoding


def encode(data: dict, encoding: str = "shift_jis", compressed: bool = True) -> bytes:
    # XML fallback is deliberately not used here: a K-bin response must retain
    # typed nodes.  This writer covers the node and scalar forms used by Pop'n.
    nodes = bytearray()
    values = bytearray()

    def stream(raw: bytes) -> None:
        values.extend(struct.pack(">I", len(raw)))
        values.extend(raw)
        values.extend(b"\0" * ((_align(len(values)) - len(values))))

    def write_node(name: str, node: dict) -> None:
        attrs = node.get("@attr", {})
        type_name = attrs.get("__type", "str" if isinstance(node.get("@content"), str) else "void")
        token = TYPES.get(type_name, 1)
        count = attrs.get("__count")
        nodes.append(token | (0x40 if count is not None else 0))
        nodes.extend(_pack_name(name, compressed, encoding))
        if type_name == "str":
            stream((str(node.get("@content", "")) + "\0").encode(encoding, errors="replace"))
        elif type_name == "bin":
            stream(bytes(node.get("@content", b"")))
        elif type_name in NUMBER_TYPES:
            fmt = NUMBER_TYPES[type_name][1]
            content = node.get("@content", [])
            content = content if isinstance(content, list) else [content]
            raw = b"".join(struct.pack(">" + fmt, value) for value in content)
            if count is not None:
                values.extend(struct.pack(">I", len(raw)))
            values.extend(raw)
            values.extend(b"\0" * (_align(len(values)) - len(values)))
        for key, value in sorted(attrs.items()):
            if key.startswith("__"):
                continue
            stream((str(value) + "\0").encode(encoding, errors="replace"))
            nodes.append(TYPES["attr"])
            nodes.extend(_pack_name(key, compressed, encoding))
        for key, value in node.items():
            if key.startswith("@"):
                continue
            for item in (value if isinstance(value, list) else [value]):
                write_node(key, item)
        nodes.extend((TYPES["nodeEnd"] | 0x40,))

    root_name = next(iter(data))
    write_node(root_name, data[root_name])
    nodes.extend((TYPES["endSection"] | 0x40,))
    header = bytearray((SIGNATURE, 0x42 if compressed else 0x45, ENCODING_VALUES.get(encoding, 0x80), 0))
    header[3] = 0xFF ^ header[2]
    header.extend(struct.pack(">I", len(nodes)))
    return bytes(header) + bytes(nodes) + struct.pack(">I", len(values)) + bytes(values)
