from dataclasses import dataclass


@dataclass
class Function:
    start: int
    end: int
    name: str
    type: str


functions: list[Function] = []

TYPE_TO_NAME = {
    "O": "Original",
    "U": "Unused",
    "R": "Replicated",
    "T": "To Be Replicated"
}

with open("stats.txt", "r") as f:
    for line in f.readlines():
        if line.startswith("#") or not line.strip():
            continue
        start, end, type, name = line.split(" ", 3)
        start = int(start, 16)
        end = int(end, 16)
        functions.append(
            Function(start, end, name, TYPE_TO_NAME[type.upper()]))

TEXT_START = 0x00401000
TEXT_END = 0x00C0F000


def compute_total(type):
    global functions
    total = 0
    for func in functions:
        if func.type == type:
            total += func.end - func.start
    return total


ratio = (compute_total("Replicated") + compute_total("Original")) / \
    (TEXT_END-TEXT_START-compute_total("Unused"))
print(f"Replicated: {ratio*100:.3f}%")
print(f"Unused functions bytes:\t\t{compute_total("Unused")}")
print(f"Replicated functions bytes:\t{compute_total("Replicated")}")
print(f"Original functions bytes:\t{compute_total("Original")}")
print(f"To be replicated:\t\t{compute_total("To Be Replicated")}")
