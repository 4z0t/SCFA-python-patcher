import os
import sys
from pathlib import Path
import re


LOC_ADDR_RE = re.compile("loc_([0-9a-fA-F]){1,6}")
SPACES_RE = re.compile(" +")


def get_log_path(args: list[str]) -> str:
    found = False
    for arg in args:
        if found:
            return arg
        if arg == "/log":
            found = True
            continue
    return None


def extract_crash_data(log_path: Path) -> list[str]:
    result = []
    with open(log_path, "r") as log_file:
        line = ""
        while not line.startswith("Exit code:"):
            line = log_file.readline()

        while not line.startswith("MiniDump:"):
            result.append(line)
            line = log_file.readline()

    return result


def load_exe_map(map_path: Path) -> list[tuple[int, str]]:
    map: list[tuple[int, str]] = []
    with open(map_path, "r") as map_file:
        line = map_file.readline()
        while line:
            line = line.strip()
            address, name = line.split(" ", 1)
            map.append((int(address, 16), name))
            line = map_file.readline()
    return map


def load_sect_map(map_path: Path) -> list[tuple[int, str]]:
    map: list[tuple[int, str]] = []
    is_text = False
    with open(map_path, "r") as map_file:
        line = map_file.readline()
        while line:
            cur_line = line.strip()
            line = map_file.readline()
            if cur_line.startswith(".text"):
                is_text = True
                continue
            if not cur_line.startswith("0x"):
                is_text = False
                continue

            if is_text:
                cur_line = SPACES_RE.sub(" ", cur_line)
                address, name = cur_line.split(" ", 1)
                map.append((int(address, 16), name))
    return map


def get_stack_trace(data: list[str]) -> list[int]:
    stack_trace = []
    for line in data:
        if line.startswith("Stacktrace:"):
            _, * trace = line.split(" ")
            stack_trace.extend((int(i, 16) for i in trace))
            break
    return stack_trace


def format_stack_trace(trace: list[int], names: list[tuple[int, str]]) -> str:
    def find_name(address: int) -> tuple[int, str]:
        start = 0
        end = len(names)
        while True:
            middle = (start+end)//2
            addr, name = names[middle]
            if addr > address:
                end = middle
            else:
                start = middle

            if end - start <= 1:
                return names[start]
    s = []
    for addr in trace:
        address, name = find_name(addr)
        s.append(f"{address:08x}\t{name}")
    return "\n".join(s)


def main(args):

    code = os.system(" ".join(args))

    if code == 0:
        return

    log_file_name = get_log_path(args)
    if log_file_name is None:
        print("Couldn't find log file name")
        return

    log_path = Path(log_file_name)
    data = extract_crash_data(log_path)
    for line in data[::-1]:
        if line.strip() == "":
            data.pop()
        else:
            break

    exe_map = load_exe_map(Path("./result.map"))
    sect = load_sect_map(Path("./FA-Binary-Patches")/"build"/"sectmap.txt")
    exe_map.extend(sect)

    stack_trace = get_stack_trace(data)
    s = format_stack_trace(stack_trace, exe_map)
    print("".join(data))
    print(s)


if __name__ == "__main__":
    # exe_map = load_exe_map(Path("./result.map"))
    # sect = load_sect_map(Path("./FA-Binary-Patches")/"build"/"sectmap.txt")
    # exe_map.extend(sect)

    # stack_trace = get_stack_trace(
    #     ["Stacktrace: 0x0043A15E 0x0043A61F 0x00438BDA 0x01291624 0x0128BC19 0x0128BC23 0x00914415 0x0092B2DF"])
    # print(format_stack_trace(stack_trace, exe_map))
    # pass
    main(sys.argv[1:])
