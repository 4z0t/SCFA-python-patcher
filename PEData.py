from dataclasses import dataclass
from typing import Optional, Any
import struct
from BasicBinaryParser import BasicBinaryParser


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

    def parse_sects_data(self):
        self.pos += 0x3c
        self.offset = self.read_uint()

        self.pos = self.offset + 0x6
        sect_count = self.value("H")

        self.pos = self.offset + 0x34
        self.imgbase, self.sectalign, self.filealign = self.values("3I")

        self.pos = self.offset + 0xf8
        for i in range(sect_count):
            self.sects.append(PESect.from_bytes(self.read_bytes(40)))

    def find_sect(self, name: str) -> Optional[PESect]:
        for sect in self.sects:
            if sect.name == name:
                return sect
        return None
