"""Shablon binaryga ishtirokchining shaxsiy flagini shifrlab yozadi."""

import os

MARKER = b"@@ZAFAR_VAULT@@!"
DATA_LEN = 48


def _rol3(x: int) -> int:
    return ((x << 3) | (x >> 5)) & 0xFF


def encode(flag: bytes, key: bytes) -> bytes:
    return bytes((_rol3(b ^ key[i % 4]) + i * 7) & 0xFF for i, b in enumerate(flag))


def build_binary(template: bytes, flag: str) -> bytes:
    raw = flag.encode()
    if len(raw) > DATA_LEN:
        raise ValueError("flag juda uzun")
    pos = template.find(MARKER)
    if pos < 0 or template.find(MARKER, pos + 1) >= 0:
        raise ValueError("shablonda marker topilmadi yoki bir nechta")
    key = os.urandom(4)
    data = encode(raw, key) + os.urandom(DATA_LEN - len(raw))
    # Markerni ham tasodifiy baytlar bilan yopamiz — grep bilan topilmasin.
    blob = os.urandom(len(MARKER)) + bytes([len(raw)]) + key + data
    return template[:pos] + blob + template[pos + len(blob):]
