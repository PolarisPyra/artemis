from .misc import assert_true


WINDOW_SIZE = 0x1000
WINDOW_MASK = WINDOW_SIZE - 1
THRESHOLD = 3
INPLACE_THRESHOLD = 0xA
LOOK_RANGE = 0x200
MAX_LEN = 0xF + THRESHOLD
MAX_BUFFER = 0x10 + 1


def match_current(window: bytes, pos: int, max_len: int, data: bytes, dpos: int) -> int:
    length = 0
    while (
        dpos + length < len(data)
        and length < max_len
        and window[(pos + length) & WINDOW_MASK] == data[dpos + length]
        and length < MAX_LEN
    ):
        length += 1
    return length


def match_window(window: bytes, pos: int, data: bytes, d_pos: int) -> None | tuple[int, int]:
    max_pos = 0
    max_len = 0
    for i in range(THRESHOLD, LOOK_RANGE):
        length = match_current(window, (pos - i) & WINDOW_MASK, i, data, d_pos)
        if length >= INPLACE_THRESHOLD:
            return (i, length)
        if length >= THRESHOLD:
            max_pos = i
            max_len = length
    if max_len >= THRESHOLD:
        return (max_pos, max_len)
    return None


def lz77_compress(data: bytes) -> bytes:
    output = bytearray()
    window = bytearray(WINDOW_SIZE)
    current_pos = 0
    current_window = 0
    current_buffer = 0
    flag_byte = 0
    bit = 0
    buffer = [0] * MAX_BUFFER
    pad = 3
    while current_pos < len(data):
        flag_byte = 0
        current_buffer = 0
        for bit_pos in range(8):
            if current_pos >= len(data):
                pad = 0
                flag_byte = flag_byte >> (8 - bit_pos)
                buffer[current_buffer] = 0
                buffer[current_buffer + 1] = 0
                current_buffer += 2
                break
            else:
                found = match_window(window, current_window, data, current_pos)
                if found is not None and found[1] >= THRESHOLD:
                    pos, length = found

                    byte1 = pos >> 4
                    byte2 = (((pos & 0x0F) << 4) | ((length - THRESHOLD) & 0x0F))
                    buffer[current_buffer] = byte1
                    buffer[current_buffer + 1] = byte2
                    current_buffer += 2
                    bit = 0
                    for _ in range(length):
                        window[current_window & WINDOW_MASK] = data[current_pos]
                        current_pos += 1
                        current_window += 1
                else:
                    buffer[current_buffer] = data[current_pos]
                    window[current_window] = data[current_pos]
                    current_pos += 1
                    current_window += 1
                    current_buffer += 1
                    bit = 1

            flag_byte = (flag_byte >> 1) | ((bit & 1) << 7)
            current_window = current_window & WINDOW_MASK

            assert_true(current_buffer < MAX_BUFFER, f"current buffer {current_buffer} > max buffer {MAX_BUFFER}")

        output.append(flag_byte)
        for i in range(current_buffer):
            output.append(buffer[i])
    for _ in range(pad):
        output.append(0)

    return bytes(output)


def lz77_decompress(data: bytes) -> bytes:
    output = bytearray()
    cur_byte = 0
    window = bytearray(WINDOW_SIZE)
    window_cursor = 0

    while cur_byte < len(data):
        flag = data[cur_byte]
        cur_byte += 1

        for i in range(8):
            if (flag >> i) & 1 == 1:
                output.append(data[cur_byte])
                window[window_cursor] = data[cur_byte]
                window_cursor = (window_cursor + 1) & WINDOW_MASK
                cur_byte += 1
            else:
                w = ((data[cur_byte]) << 8) | (data[cur_byte + 1])
                if w == 0:
                    return bytes(output)

                cur_byte += 2
                position = ((window_cursor - (w >> 4)) & WINDOW_MASK)
                length = (w & 0x0F) + THRESHOLD

                for _ in range(length):
                    b = window[position & WINDOW_MASK]
                    output.append(b)
                    window[window_cursor] = b
                    window_cursor = (window_cursor + 1) & WINDOW_MASK
                    position += 1

    return bytes(output)


__all__ = (
    "lz77_compress", "lz77_decompress"
)
