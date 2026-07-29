import binascii

from Crypto.Cipher import DES3

from .misc import assert_true, pack, unpack
from .exception import InvalidCard
from .const import CARD_ALPHABET


def enc_des(uid: bytes, key: bytes) -> bytes:
    key = bytes(i * 2 for i in key)
    cipher = DES3.new(key, DES3.MODE_CBC, iv=b'\0' * 8)
    return cipher.encrypt(uid)


def dec_des(uid: bytes, key: bytes) -> bytes:
    key = bytes(i * 2 for i in key)
    cipher = DES3.new(key, DES3.MODE_CBC, iv=b'\0' * 8)
    return cipher.decrypt(uid)


def checksum(data: bytes) -> int:
    chk = sum(data[i] * (i % 3 + 1) for i in range(15))

    while chk > 31:
        chk = (chk >> 5) + (chk & 31)

    return chk


def uid_to_konami(uid: str, key: bytes) -> str:
    assert_true(len(uid) == 16, "UID must be 16 bytes", InvalidCard)

    if uid.upper().startswith("E004"):
        card_type = 1
    elif uid.upper().startswith("0"):
        card_type = 2
    else:
        raise InvalidCard("Invalid UID prefix")

    kid = binascii.unhexlify(uid)
    assert_true(len(kid) == 8, "ID must be 8 bytes", InvalidCard)

    out = bytearray(unpack(enc_des(kid[::-1], key), 5)[:13]) + b'\0\0\0'

    out[0] ^= card_type
    out[13] = 1
    for i in range(1, 14):
        out[i] ^= out[i - 1]
    out[14] = card_type
    out[15] = checksum(out)

    return "".join(CARD_ALPHABET[i] for i in out)


def konami_to_uid(konami_id: str, key: bytes) -> str:
    if konami_id[14] == "1":
        card_type = 1
    elif konami_id[14] == "2":
        card_type = 2
    else:
        raise InvalidCard("Invalid ID")

    assert_true(len(konami_id) == 16, "ID must be 16 characters", InvalidCard)
    assert_true(all(i in CARD_ALPHABET for i in konami_id), "ID contains invalid characters", InvalidCard)
    card = bytearray([CARD_ALPHABET.index(i) for i in konami_id])
    assert_true(card[11] % 2 == card[12] % 2, "Parity check failed", InvalidCard)
    assert_true(card[13] == card[12] ^ 1, "Card invalid", InvalidCard)
    assert_true(card[15] == checksum(card), "Checksum failed", InvalidCard)

    for i in range(13, 0, -1):
        card[i] ^= card[i - 1]

    card[0] ^= card_type

    card_id = dec_des(pack(card[:13], 5)[:8], key)[::-1]
    card_id = binascii.hexlify(card_id).decode().upper()

    if card_type == 1:
        assert_true(card_id[:4] == "E004", "Invalid card type", InvalidCard)
    elif card_type == 2:
        assert_true(card_id[0] == "0", "Invalid card type", InvalidCard)
    return card_id


__all__ = ("konami_to_uid", "uid_to_konami")
