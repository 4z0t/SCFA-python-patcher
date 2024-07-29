import sys
import os
from pathlib import Path
import re
from typing import Optional
from PEFile import PEFile

FLAGS = "-pipe -m32 -Os -nostartfiles -w -fpermissive -masm=intel -std=c++20 -march=core2 -stdlib++-isystem C:/msys64/mingw64/include/c++/13.2.0 -I C:/msys64/mingw64/include/c++/13.2.0/x86_64-w64-mingw32 -L C:\msys64\mingw32\lib -L C:\msys64\mingw32\lib\gcc\i686-w64-mingw32\\13.1.0"


def scan_header_files(target_path: str):
    functions_addresses = []
    contents = read_files_contents(
        f"{target_path}/section/include/",
        list_files_at(f"{target_path}/section/include/", "**/*.h"))

    for line in contents:
        matches = re.finditer(
            r"(asm\(\"(0[xX][0-9a-fA-F]{1,8})\"\);)", line, re.IGNORECASE)
        for match in matches:
            functions_addresses.append(match.group(2))  # get address
    return functions_addresses


def list_files_at(folder: str, pattern: str, excluded: Optional[list[str]] = None):
    dir_path = Path(folder)
    pathlist = dir_path.glob(pattern)

    paths = [path.name for path in pathlist]
    if excluded is not None:
        paths = [path for path in paths if path not in excluded]
    return paths


def find_patch_files(dir_path_s: str):
    return list_files_at(dir_path_s, "**/*.cpp", ["main.cpp"])


def read_files_contents(dir_path, paths):
    files_contents = []
    for path in paths:
        with open(dir_path + path, "r")as f:
            files_contents.extend(f.readlines())

    return files_contents


def preprocess_lines(lines: list[str]):
    new_lines = []
    address_names = {}
    for line in lines:

        matches = re.finditer(
            r"((call|jmp|je|jne)\s+(0[xX][0-9a-fA-F]{1,8}))", line, re.IGNORECASE)

        new_line = line
        for match in matches:
            full_s = match.group(0)
            address = match.group(3)
            address_name = "_" + address[1::]
            s_start, s_end = match.span()
            address_names[address_name] = address
            new_line = new_line[:s_start] + \
                full_s.replace(address, address_name) + new_line[s_end:]

        new_lines.append(new_line)
    return new_lines, address_names


def create_sections_file(path, address_map):

    HEADER = """
    OUTPUT_FORMAT(pei-i386)
    OUTPUT(section.pe)
    """
    FUNC_NAMES = """
    _atexit  = 0xA8211E;
    __Znwj   = 0xA825B9;
    __ZdlPvj = 0x958C40;
    "__imp__GetModuleHandleA@4" = 0xC0F378;
    "__imp__GetProcAddress@8" = 0xC0F48C;
    """
    SECTIONS = """
    SECTIONS {
        . = __image_base__ + 0x1000;
        .text : {
            *(.text*)
            *(.data*)
            *(.bss*)
            *(.rdata)
        }
        /DISCARD/ : {
            *(.rdata$zzz)
            *(.eh_frame*)
            *(.ctors)
            *(.reloc)
            *(.idata*)
        }
    }
    """

    with open(path, "w") as f:
        f.write(HEADER)
        f.write(FUNC_NAMES)
        for name, address in address_map.items():
            f.write(f"\"{name}\" = {address};\n")
        f.write(SECTIONS)


def parse_sect_map(file_path):
    addresses = {}
    with open(file_path, "r") as f:
        line = f.readline()
        while not line.startswith(" .text"):
            line = f.readline()

        line = f.readline()
        while not line.startswith(" *(.data*)"):
            address, name = re.sub(" +", " ", line.strip()).split(" ")
            name = name.split("(")[0]

            if name in addresses:
                raise Exception(f"Duplicated name for patch function {name}")

            addresses[name] = address

            line = f.readline()

    return addresses


def main(_, target_path, compiler_path, *args):
    paths = find_patch_files(f"{target_path}/section/")

    files_contents = read_files_contents(f"{target_path}/section/", paths)
    files_contents, address_names = preprocess_lines(files_contents)

    with open(f"{target_path}/section/main.cpp", "w") as main_file:
        main_file.writelines(files_contents)

    function_addresses = {
        name: name for name in scan_header_files(target_path)}

    create_sections_file(f"{target_path}/section.ld",
                         address_names | function_addresses)
    print(os.system(
        f"cd {target_path}/build & {compiler_path} {FLAGS} -Wl,-T,../section.ld,--image-base,45000,-s,-Map,../sectmap.txt ../section/main.cpp"))

    addresses = parse_sect_map(f"{target_path}/sectmap.txt")
    print(addresses)

    print(os.system(
        f"cd {target_path}/build & {compiler_path} -c {FLAGS} ../hooks/*.cpp"))


if __name__ == "__main__":
    main(*sys.argv)
