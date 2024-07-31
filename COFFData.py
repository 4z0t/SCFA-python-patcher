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


class COFFData(BasicBinaryParser):
    def __init__(self, file_path: str) -> None:
        data: bytes = None
        self.name: str = file_path
        self.sects: list[COFFSect] = []
        with open(file_path, "rb") as f:
            data = f.read()

        if data is None:
            raise Exception(f"Couldn't read data from file {file_path}")

        super().__init__(data)

        self.parse_sects_data()

    def parse_sects_data(self):
        self.pos = 2
        sect_count = self.value("H")
        self.pos = 20
        for i in range(sect_count):
            name = self.value("8s").decode().replace("\x00", "")
            if name[0] == "h":
                self.sects.append(COFFSect(name, 0, 0))
            self.pos += 0x20

        self.pos = 8
        pos, count = self.values("II")
        self.pos = pos

        for i in range(count):
            pass

    def find_sect(self, name) -> Optional[COFFSect]:
        for sect in self.sects:
            if sect.name == name:
                return sect
        return None
