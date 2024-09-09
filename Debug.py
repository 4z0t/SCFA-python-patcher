import os
import sys
from pathlib import Path


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
    print("".join(data))


if __name__ == "__main__":
    main(sys.argv[1:])
