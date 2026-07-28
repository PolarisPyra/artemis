"""Konami e-amusement request encryption.

This mirrors Asphyxia CORE's ``KonmaiEncrypt`` implementation.  The protocol
uses an RC4-style stream generated from the six key bytes in X-Eamuse-Info.
"""

from __future__ import annotations

import hashlib
import secrets


class KonmaiEncrypt:
    def __init__(self, public_key: str | None = None) -> None:
        key = bytearray(
            bytes.fromhex(
                "00000000000069d74627d985ee2187161570d08d93b12455035b6df0d8205df5"
            )
        )
        if public_key:
            parts = public_key.split("-")
            if len(parts) >= 3:
                raw = parts[1] + parts[2]
                try:
                    key[:6] = bytes.fromhex(raw[:12])
                except ValueError:
                    pass
        else:
            key[:6] = secrets.token_bytes(6)

        self._key = bytes(key)
        self._real_key = hashlib.md5(self._key).digest()

    @property
    def public_key(self) -> str:
        return f"1-{self._key[:4].hex()}-{self._key[4:6].hex()}"

    def crypt(self, data: bytes) -> bytes:
        state = list(range(256))
        t = 0
        for index in range(256):
            t = (t + state[index] + self._real_key[index % len(self._real_key)]) % 256
            state[index], state[t] = state[t], state[index]

        i = j = 0
        result = bytearray(len(data))
        for index, value in enumerate(data):
            i = (i + 1) % 256
            j = (j + state[i]) % 256
            state[i], state[j] = state[j], state[i]
            result[index] = value ^ state[(state[i] + state[j]) % 256]
        return bytes(result)
