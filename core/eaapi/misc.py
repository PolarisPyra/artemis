import inspect
import re

from typing import Type

from .exception import CheckFailed, InvalidModel


def assert_true(check: bool, reason: str, exc: Type[Exception] = CheckFailed):
    if not check:
        line = inspect.stack()[1].code_context
        if line:
            print()
            print("\n".join(line))
        raise exc(reason)


def py_encoding(name: str) -> str:
    if name.startswith("shift-jis"):
        return "shift-jis"
    return name


def parse_model(model: str) -> tuple[str, str, str, str, str]:
    # e.g. KFC:J:A:A:2019020600
    match = re.match(r"^([A-Z0-9]{3}):([A-Z]):([A-Z]):([A-Z])(?::(\d{10}))?$", model)
    if match is None:
        raise InvalidModel
    gamecode, dest, spec, rev, datecode = match.groups()
    return gamecode, dest, spec, rev, datecode


def pack(data, width: int) -> bytes:
    assert_true(1 <= width <= 8, "Invalid pack size")
    assert_true(all(i < (1 << width) for i in data), "Data too large for packing")
    bit_buf = in_buf = 0
    output = bytearray()
    for i in data:
        bit_buf |= i << (8 - width)
        shift = min(8 - in_buf, width)
        bit_buf <<= shift
        in_buf += shift
        if in_buf == 8:
            output.append(bit_buf >> 8)
            in_buf = width - shift
            bit_buf = (bit_buf & 0xff) << in_buf

    if in_buf:
        output.append(bit_buf >> in_buf)

    return bytes(output)


def unpack(data, width: int) -> bytes:
    assert_true(1 <= width <= 8, "Invalid pack size")
    bit_buf = in_buf = 0
    output = bytearray()
    for i in data:
        bit_buf |= i
        bit_buf <<= width - in_buf
        in_buf += 8
        while in_buf >= width:
            output.append(bit_buf >> 8)
            in_buf -= width
            bit_buf = (bit_buf & 0xff) << min(width, in_buf)

    if in_buf:
        output.append(bit_buf >> (8 + in_buf - width))

    return bytes(output)


__all__ = ("assert_true", "py_encoding", "parse_model", "pack", "unpack")
