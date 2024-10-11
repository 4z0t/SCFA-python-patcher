import re
from pathlib import Path

ADDRESS_RE = re.compile(r"^#(0[xX][0-9A-Fa-f]{6,8})\:$")
FUNCTION_NAME_RE = re.compile(r"@([a-zA-Z\_][a-zA-Z0-9\_]+)")


class Section:

    def __init__(self, address: str, lines: list[str]) -> None:
        self._address: str = address
        self._lines: list[str] = lines

    def lines_to_cpp(self):
        s = ""
        for line in self._lines:
            line = line.translate(str.maketrans({"\"":  r"\"", "\\": r"\\", }))

            if FUNCTION_NAME_RE.findall(line):
                line = FUNCTION_NAME_RE.sub(r'"QU(\1)"', line)

            s += f'"{line};"\n'
        return s

    def to_cpp(self, index: int) -> str:
        if self._address is None:
            return self.lines_to_cpp()
        return f'SECTION({index:X}, {self._address})\n{self.lines_to_cpp()}'


class Hook:
    def __init__(self, sections: list[Section]) -> None:
        self._sections: list[Section] = sections

    def to_cpp(self):
        s = '#include "../asm.h"\n#include "../define.h"\n'
        sections_lines = (section.to_cpp(i).split("\n")
                          for i, section in enumerate(self._sections))
        s += f"asm(\n{''.join((f"    {line}\n" for lines in sections_lines for line in lines))});"
        return s


def load_hook(file_path: Path) -> Hook:
    sections: list[Section] = []
    lines = []
    address = None
    with open(file_path) as f:
        for line in f.readlines():
            # remove comments
            line = line.split("//")[0]
            if not line.startswith("#"):
                line = line.split("#")[0]
            line = line.strip()
            if not line:
                continue

            if match := ADDRESS_RE.match(line):
                sections.append(Section(address, lines))
                lines = []
                address = match.group(1)
                continue
            lines.append(line)
        sections.append(Section(address, lines))
        return Hook(sections)
