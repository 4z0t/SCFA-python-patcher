from dataclasses import dataclass
from typing import Optional, Any
import struct


class BasicBinaryParser:

    def __init__(self, bytes: bytes) -> None:
        self._data: bytes = bytes
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

    def value(self, type: str) -> Any:
        return struct.unpack(type, self.read_bytes(struct.calcsize(type)))[0]


@dataclass
class PESect:
    name: str
    v_size: int
    v_offset: int
    f_size: int
    f_offset: int
    flags: int

    @staticmethod
    def from_bytes(b: bytes):
        assert struct.calcsize("8s4i12xI") == 40

        name, v_size, v_offset, f_size, f_offset, flags =\
            struct.unpack("8s4i12xI", b)
        return PESect(
            name=name.decode().replace("\x00", ""),
            v_size=v_size,
            v_offset=v_offset,
            f_size=f_size,
            f_offset=f_offset,
            flags=flags)


class PEData(BasicBinaryParser):
    def __init__(self, file_path: str) -> None:

        data: bytes = None
        self.offset: int = 0
        self.imgbase: int = 0
        self.sectalign: int = 0
        self.filealign: int = 0
        self.sects: list[PESect] = []

        with open(file_path, "rb") as f:
            data = f.read()

        if data is None:
            raise Exception(f"Couldn't read data from file {file_path}")

        super().__init__(data)

        self.parse_sects_data()

    def read_int(self):
        return self.value("i")

    def read_uint(self):
        return self.value("I")

    def parse_sects_data(self):
        self._pos += 0x3c
        self.offset = self.read_uint()

        self._pos = self.offset + 0x6
        sect_count = self.value("H")

        self._pos = self.offset + 0x34
        self.imgbase = self.read_uint()
        self.sectalign = self.read_uint()
        self.filealign = self.read_uint()

        self._pos = self.offset + 0xf8
        for i in range(sect_count):
            b = self.read_bytes(40)
            self.sects.append(PESect.from_bytes(b))

    def find_sect(self, name: str) -> Optional[PESect]:
        for sect in self.sects:
            if sect.name == name:
                return sect
        return None
