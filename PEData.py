from dataclasses import dataclass
from typing import Optional


class PESect:
    name: str
    v_size: int
    v_offset: int
    f_size: int
    f_offset: int
    pad: bytes
    flags: int

    @staticmethod
    def from_bytes(b: bytes):
        pesect = PESect()
        pesect.name = b[0:8].decode().replace("\x00", '')
        pesect.v_size = int.from_bytes(b[8:12], "little", signed=True)
        pesect.v_offset = int.from_bytes(b[12:16], "little", signed=True)
        pesect.f_size = int.from_bytes(b[16:20], "little", signed=True)
        pesect.f_offset = int.from_bytes(b[20:24], "little", signed=True)
        pesect.pad = b[24:36]
        pesect.flags = int.from_bytes(b[36:40], "little", signed=False)
        return pesect


class PEData:
    def __init__(self, file_path: str) -> None:

        self._data: bytes = None
        self._pos: int = 0
        self.offset: int = 0
        self.imgbase: int = 0
        self.sectalign: int = 0
        self.filealign: int = 0
        self.sects: list[PESect] = []

        with open(file_path, "rb") as f:
            self._data = f.read()
        if self._data is None:
            raise Exception(f"Couldn't read data from file {file_path}")

        self.parse_sects_data()

    def read_bytes(self, size: int):
        b = self._data[self._pos:self._pos+size]
        self._pos += size
        return b

    def read_int(self):
        return int.from_bytes(self.read_bytes(4), "little", signed=True)

    def read_uint(self):
        return int.from_bytes(self.read_bytes(4), "little", signed=False)

    def parse_sects_data(self):
        self._pos += 0x3c
        self.offset = self.read_uint()

        self._pos = self.offset + 0x6
        sect_count = int.from_bytes(self.read_bytes(2), "little", signed=False)

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
