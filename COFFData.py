from dataclasses import dataclass
from typing import Optional, Any
import struct
from BasicBinaryParser import BasicBinaryParser


@dataclass
class COFFSect:
    name: str
    size: int
    offset: int

    @staticmethod
    def from_bytes(b: bytes):
        assert struct.calcsize("8s2I") == 16

        name, size, offset = struct.unpack("8s2I", b)
        return COFFSect(name=name.decode().replace("\x00", ""),
                        size=size,
                        offset=offset)


class COFFData:
    def __init__(self, file_path: str) -> None:
        pass
