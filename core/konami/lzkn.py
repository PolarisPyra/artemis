"""LZ-KN compressor/decompressor used by e-amusement clients."""

from __future__ import annotations


WINDOW_SIZE = 0x1000
WINDOW_MASK = WINDOW_SIZE - 1


def inflate(data: bytes) -> bytes:
    result = bytearray()
    cursor = 0
    flags = 1
    while True:
        if flags == 1:
            if cursor >= len(data):
                break
            flags = data[cursor] | 0x100
            cursor += 1
        literal = flags & 1
        flags >>= 1
        if literal:
            if cursor >= len(data):
                break
            result.append(data[cursor])
            cursor += 1
            continue

        if cursor + 1 >= len(data):
            break
        byte1, byte2 = data[cursor], data[cursor + 1]
        cursor += 2
        length = (byte2 & 0x0F) + 3
        distance = ((byte1 << 4) & 0x0FF0) | (byte2 >> 4)
        if distance == 0:
            break
        for _ in range(length):
            result.append(result[-distance] if distance <= len(result) else 0)
    return bytes(result)


def deflate_dummy(data: bytes) -> bytes:
    """Emit the literal-only form accepted by Asphyxia clients."""
    output = bytearray()
    full, remainder = divmod(len(data), 8)
    for index in range(full):
        output.append(0xFF)
        output.extend(data[index * 8 : index * 8 + 8])
    if remainder:
        output.append(0xFF >> (8 - remainder))
        output.extend(data[-remainder:])
        output.extend(b"\0" * 4)
    else:
        output.extend(b"\0" * 8)
    return bytes(output)


def deflate(data: bytes) -> bytes:
    """Compress using the same 4 KiB sliding-window format as Asphyxia."""
    window = bytearray(WINDOW_SIZE)
    output = bytearray()
    cursor = window_cursor = 0
    while cursor < len(data):
        flags = 0
        chunk = bytearray()
        for bit in range(8):
            if cursor >= len(data):
                break
            best_distance = best_length = 0
            for distance in range(3, min(0x200, cursor + 1)):
                length = 0
                while (
                    length < 18
                    and cursor + length < len(data)
                    and window[(window_cursor - distance + length) & WINDOW_MASK]
                    == data[cursor + length]
                ):
                    length += 1
                if length >= 10:
                    best_distance, best_length = distance, length
                    break
                if length >= 3 and length > best_length:
                    best_distance, best_length = distance, length
            if best_length >= 3:
                chunk.extend(
                    (
                        (best_distance >> 4) & 0xFF,
                        ((best_distance & 0x0F) << 4) | (best_length - 3),
                    )
                )
                for _ in range(best_length):
                    window[window_cursor] = data[cursor]
                    cursor += 1
                    window_cursor = (window_cursor + 1) & WINDOW_MASK
            else:
                # The wire format is consumed least-significant bit first.
                flags |= 1 << bit
                chunk.append(data[cursor])
                window[window_cursor] = data[cursor]
                cursor += 1
                window_cursor = (window_cursor + 1) & WINDOW_MASK
        output.append(flags)
        output.extend(chunk)
    output.extend(b"\0\0\0")
    return bytes(output)
