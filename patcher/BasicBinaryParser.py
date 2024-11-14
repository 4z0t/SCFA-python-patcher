from dataclasses import dataclass
from typing import Optional, Any
import struct


class BasicBinaryParser:

    def __init__(self, data: bytes) -> None:
        self._data: bytes = data
        self._pos: int = 0

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, pos) -> None:
        self._pos = pos

    def read_bytes(self, size: int) -> bytes:
        b = self._data[self._pos:self._pos+size]
        self._pos += size
        return b

    def values(self, type: str) -> tuple[Any, ...]:
        return struct.unpack(type, self.read_bytes(struct.calcsize(type)))

    def value(self, type: str) -> Any:
        return self.values(type)[0]

    def read_int(self):
        return self.value("i")

    def read_uint(self):
        return self.value("I")
