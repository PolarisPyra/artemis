import binascii
import hashlib
import time
import re

from Crypto.Cipher import ARC4

from .misc import assert_true


def new_prng():
    state = 0x41c64e6d

    while True:
        x = (state * 0x838c9cda) + 0x6072
        # state = (state * 0x41c64e6d + 0x3039)
        # state = (state * 0x41c64e6d + 0x3039)
        state = (state * 0xc2a29a69 + 0xd3dc167e) & 0xffffffff
        yield (x & 0x7fff0000) | state >> 15 & 0xffff


prng = new_prng()


def validate_key(info):
    match = re.match(r"^(\d)-([0-9a-f]{8})-([0-9a-f]{4})$", info)
    assert_true(match is not None, "Invalid eamuse info key")
    assert match is not None
    version = match.group(1)
    assert_true(version == "1", f"Unsupported encryption version ({version})")

    seconds = binascii.unhexlify(match.group(2))  # 4 bytes
    rng = binascii.unhexlify(match.group(3))  # 2 bytes
    return seconds, rng


def get_key(prng_=None):
    return f"1-{int(time.time()):08x}-{(next(prng_ or prng) & 0xffff):04x}"


def ea_symmetric_crypt(data, info, secret: bytes):
    seconds, rng = validate_key(info)

    key = hashlib.md5(seconds + rng + secret).digest()

    return ARC4.new(key).encrypt(data)


__all__ = ("new_prng", "prng", "validate_key", "get_key", "ea_symmetric_crypt")
