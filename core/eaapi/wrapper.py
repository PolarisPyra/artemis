from .crypt import ea_symmetric_crypt
from .lz77 import lz77_compress, lz77_decompress


def wrap(packet: bytes, info: str | None = None, compressed: bool = True) -> bytes:
    if compressed:
        packet = lz77_compress(packet)
    if info is None:
        return packet
    return ea_symmetric_crypt(packet, info)


def unwrap(packet: bytes, info: str | None = None, compressed: bool = True) -> bytes:
    if info is None:
        decrypted = packet
    else:
        decrypted = ea_symmetric_crypt(packet, info)

    if compressed is None:
        try:
            decompressed = lz77_decompress(decrypted)
        except IndexError:
            return decrypted
        if decompressed == b"\0\0\0\0\0\0":
            # Decompression almost certainly failed
            return decrypted
        return decompressed
    return lz77_decompress(decrypted) if compressed else decrypted


__all__ = ("wrap", "unwrap")
