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
    "X": "Unmarked",
    "N": "Not Done"
}

TEXT_START = 0x00401000
TEXT_END = 0x00C0F000


def read_file_functions_data(file_path) -> list[Function]:
    functions = []
    fn = None
    with open(file_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            start, type, name = line.split(" ", 2)
            start = int(start, 16)
            if fn is not None:
                fn.end = start
            fn = Function(start, 0, name, type.upper())
            functions.append(fn)
    if fn is not None:
        fn.end = TEXT_END
    return functions


def read_file_functions_data_with_end(file_path) -> list[Function]:
    functions = []
    with open(file_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            start, end, type, name = line.split(" ", 3)
            start = int(start, 16)
            end = int(end, 16)
            fn = Function(start, end, name, type.upper())
            functions.append(fn)
    return functions


def write_file_functions_data(file_path, functions: list[Function]):
    with open(file_path, "w") as f:
        for fn in functions:
            f.write(f"{fn.start:08x} {fn.type} {fn.name}\n")
    return functions


def merge_stats(file_dest, file_source) -> list[Function]:
    initial = read_file_functions_data(file_dest)

    def find_by_start(start):
        for i, fn in enumerate(initial):
            if fn.start == start:
                return i
        return None

    new_functions = read_file_functions_data_with_end(file_source)
    for fn in new_functions:
        i = find_by_start(fn.start)
        if i is not None:
            initial.pop(i)

    initial.extend(new_functions)

    initial.sort(key=lambda fn: fn.start)
    write_file_functions_data(file_dest, initial)
    return initial


functions = merge_stats("stats3.txt", "stats.txt")


def compute_total(functions, type):
    total = 0
    for func in functions:
        if func.type == type:
            total += func.end - func.start
    return total


ratio = (compute_total(functions, "R") + compute_total(functions, "O") + compute_total(functions, "T")) / \
    (TEXT_END-TEXT_START-compute_total(functions, "U"))
print(f"Replicated: {ratio*100:.3f}%")
print(f"Unused functions bytes:\t\t{compute_total(functions, "U")}")
print(f"Replicated functions bytes:\t{compute_total(functions, "R")}")
print(f"Original functions bytes:\t{compute_total(functions, "O")}")
print(f"To be replicated:\t\t{compute_total(functions, "T")}")
print(f"Unknown:\t\t{(compute_total(functions, "X")) /
      (TEXT_END-TEXT_START)*100:.3f}%")
