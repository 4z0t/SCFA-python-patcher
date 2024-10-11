from dataclasses import dataclass


@dataclass
class Function:
    start: int
    end: int
    name: str
    type: str


TYPE_TO_NAME = {
    "O": "Original",
    "U": "Unused",
    "R": "Replicated",
    "T": "To Be Replicated",
    "X": "Unmarked"
}

TEXT_START = 0x00401000
TEXT_END = 0x00C0F000


def compute_total(type):
    global functions
    total = 0
    for func in functions:
        if func.type == type:
            total += func.end - func.start
    return total


def read_file_functions_data(file_path) -> list[Function]:
    functions = []
    with open(file_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            start, end, type, name = line.split(" ", 3)
            start = int(start, 16)
            end = int(end, 16)
            functions.append(
                Function(start, end, name, type.upper()))
    return functions


def write_file_functions_data(file_path, functions: list[Function]):
    with open(file_path, "w") as f:
        for fn in functions:
            f.write(f"{fn.start:08x} {fn.end:08x} {fn.type} {fn.name}\n")
    return functions


def merge_stats(file_dest, file_source):
    initial = read_file_functions_data(file_dest)

    def find_by_start(start):
        for i, fn in enumerate(initial):
            if fn.start == start:
                return i
        return None

    new_functions = read_file_functions_data(file_source)
    for fn in new_functions:
        i = find_by_start(fn.start)
        if i is not None:
            initial.pop(i)

    initial.extend(new_functions)

    initial.sort(key=lambda fn: fn.start)
    write_file_functions_data(file_dest, initial)


merge_stats("stats2.txt", "stats.txt")
