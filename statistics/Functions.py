import re

IDA_MAP_PATH = "F:/GIT/fa_patch/ForgedAlliance_base.exe.map"
MANGLED_MAP_PATH = r"F:\GIT\fa_patch\remapped4.txt"
LOC_ADDR_RE = re.compile("loc_([0-9a-fA-F]){1,6}")

OFFSET = 0x401000

SPACES_RE = re.compile(" +")


def main():
    addresses = {}
    with open(IDA_MAP_PATH, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("0001:"):
                line = line.split(':', 1)[1]
                line = SPACES_RE.sub(" ", line)
                address, name = line.split(" ", 1)
                if not LOC_ADDR_RE.match(name):
                    address = int(f"0x{address}", 16) + OFFSET
                    addresses[address] = name

    with open(MANGLED_MAP_PATH, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0 or ".dll:" in line or ".DLL:" in line:
                continue
            line = SPACES_RE.sub(" ", line)

            name, address, *_ = line.split(" ")
            address = int(address, 16)
            addresses[address] = name
    with open("./result.map", "w") as map:
        lines = [item for item in addresses.items()]
        lines.sort(key=lambda item: item[0])
        for address, name in lines:
            map.write(f"0x{address:x} {name}\n")


if __name__ == "__main__":
    main()
