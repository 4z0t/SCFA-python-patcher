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
    def __init__(self, file_path: str, name: str = None) -> None:
        data: bytes = None
        self.name: str = name or file_path
        self.sects: list[COFFSect] = []
        with open(file_path, "rb") as f:
            data = f.read()

        if data is None:
            raise Exception(f"Couldn't read data from file {file_path}")

        super().__init__(data)

        self.parse_sects_data(file_path)

    def parse_sects_data(self, file_path: str):
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

        assert struct.calcsize("8sI5xb") == 18
        assert struct.calcsize("I14x") == 18

        i = 0
        while i < count:
            i += 1
            name, offset, c = struct.unpack("8sI5xb", self.read_bytes(18))
            name: str = name.decode().replace("\x00", "")
            sect = self.find_sect(name)

            if sect is None:
                self.pos += c * 18
                i += c
                continue

            if c > 0:
                size = struct.unpack("I14x", self.read_bytes(18))[0]
                sect.size = size
                i += 1
                continue
            sect.offset = offset

        self.pos = 20
        data = self.data
        for i in range(sect_count):
            name = struct.unpack("8s", self.read_bytes(8))[0]
            try:
                name: str = name.decode().replace("\x00", "")
            except UnicodeDecodeError:
                name = ""
            sect = self.find_sect(name)
            if sect is not None:
                self.pos += 8
                size_bytes = struct.pack("I", sect.size)
                data = data[:self.pos] + size_bytes + data[self.pos + 4:]
                continue
            self.pos += 0x20

        with open(file_path, "wb") as f:
            f.write(data)

        print(self.sects)

    def find_sect(self, name: str) -> Optional[COFFSect]:
        for sect in self.sects:
            if sect.name == name:
                return sect
        return None
