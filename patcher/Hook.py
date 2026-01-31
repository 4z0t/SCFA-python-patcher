import re
from pathlib import Path

ADDRESS_RE = re.compile(r"^(0[xX][0-9A-Fa-f]{6,8})\:$")
FUNCTION_NAME_RE = re.compile(r"@([a-zA-Z\_][a-zA-Z0-9\_]+)")
ESCAPE_TRANSLATION = str.maketrans({"\"":  r"\"", "\\": r"\\", })

class Section:

    def __init__(self, address: str, lines: list[str], addresses: dict[str, str]) -> None:
        self._address: str = address
        self._lines: list[str] = lines
        self._addresses: dict[str, str] = addresses

    def lines_to_cpp(self):
        s = []
        for line in self._lines:
            # line = line.translate(ESCAPE_TRANSLATION)

            def replace_address(match: re.Match[str]) -> str:
                func_name = match.group(1)
                if func_name in self._addresses:
                    return f'{self._addresses[func_name]} /* {func_name} */'
                return match.group(0)

            if FUNCTION_NAME_RE.findall(line):
                line = FUNCTION_NAME_RE.subn(replace_address, line)[0]

            s.append(f'{line};')
        return "\n".join(s)

    def header(self, index: int) -> str:
        return f'.section h{index:X}; .set h{index:X},{self._address};'

    def to_cpp(self, index: int) -> str:
        if self._address is None:
            return self.lines_to_cpp()
        return f'{self.header(index)}\n{self.lines_to_cpp()}'


class Hook:
    def __init__(self, sections: list[Section]) -> None:
        self._sections: list[Section] = sections

    def to_cpp(self):
        s = ''
        if len(self._sections) > 0:
            sections_lines = (section.to_cpp(i).split("\n")
                              for i, section in enumerate(self._sections))
            s += f"asm(R\"(\n{''.join((f"    {line}\n" for lines in sections_lines for line in lines))})\");"
        return s


def load_hook(file_path: Path, addresses: dict[str, str]) -> Hook:
    sections: list[Section] = []
    lines = []
    address = None
    with open(file_path) as f:
        for line in f.readlines():
            # remove comments
            line = line.split("//")[0]
            line = line.split("#")[0]
            line = line.strip()
            if not line:
                continue

            if match := ADDRESS_RE.match(line):
                if len(lines) > 0:
                    sections.append(Section(address, lines, addresses))
                lines = []
                address = match.group(1)
                continue
            lines.append(line)
        if len(lines) > 0:
            sections.append(Section(address, lines, addresses))
        return Hook(sections)
