from PEData import PEData, PESect
from COFFData import COFFData, COFFSect
import sys
import os
from pathlib import Path
import re
from typing import Optional
import struct

FLAGS = " ".join(["-pipe -m32 -Os -nostartfiles -w -fpermissive -masm=intel -std=c++20 -march=core2 -mfpmath=sse",
                  "-fseh-exceptions",
                  "-stdlib++-isystem C:/msys64/mingw64/include/c++/13.2.0",
                  "-I C:/msys64/mingw64/include/c++/13.2.0/x86_64-w64-mingw32",
                  "-L C:\msys64\mingw32\lib",
                  "-L C:\msys64\mingw32\lib\gcc\i686-w64-mingw32/13.1.0"])

HOOKS_FLAGS = " ".join(["-pipe -m32 -Os -nostartfiles -w -fpermissive -masm=intel -std=c++20 -march=core2 -mfpmath=sse",
                        ])
SECT_SIZE = 0x80000


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
            files_contents.append("\n")

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
"___CxxFrameHandler3" = 0xA8958C;
"___std_terminate" = 0xA994FB; /*idk addr*/
"??_7type_info@@6B@" = 0xD72A88;
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
         .ctors : {
            _FIRST_CTOR = .;
            *(.ctors)
            *(.CRT*)
            _END_CTOR = .;
        }
        /DISCARD/ : {
            *(.rdata$zzz)
            *(.eh_frame*)
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
            items = re.sub(
                " +", " ", line.strip()).split("(")[0].split(" ")
            if len(items) != 2:
                break

            address, name = re.sub(
                " +", " ", line.strip()).split("(")[0].split(" ")

            if name in addresses:
                raise Exception(
                    f"Duplicated name for patch function {name}")

            addresses[name] = address

            line = f.readline()

    return addresses


def main(_, target_path, compiler_path, linker_path, hooks_compiler, * args):

    base_pe = PEData(f"{target_path}/ForgedAlliance_base.exe")
    new_v_offset = 0
    new_f_offset = 0

    for sect in base_pe.sects:
        new_v_offset = max(sect.v_offset + sect.v_size, new_v_offset)
        new_f_offset = max(sect.f_offset + sect.f_size, new_f_offset)

    def align(v, a):
        return (v + a-1) & (~(a-1))

    new_v_offset = align(new_v_offset, base_pe.sectalign)
    new_f_offset = align(new_f_offset, base_pe.filealign)

    paths = find_patch_files(f"{target_path}/section/")

    files_contents = read_files_contents(f"{target_path}/section/", paths)
    files_contents, address_names = preprocess_lines(files_contents)

    with open(f"{target_path}/section/main.cpp", "w") as main_file:
        main_file.writelines(files_contents)

    function_addresses = {
        name: name for name in scan_header_files(target_path)}

    create_sections_file(f"{target_path}/section.ld",
                         address_names | function_addresses)
    print(f"Image base: {base_pe.imgbase + new_v_offset - 0x1000:x}")
    if (os.system(
            f"cd {target_path}/build & {compiler_path} {FLAGS} -Wl,-T,../section.ld,--image-base,{base_pe.imgbase + new_v_offset - 0x1000},-s,-Map,../sectmap.txt,-o,section.pe ../section/main.cpp")):
        raise Exception("Errors occured during building of patch files")

    addresses = parse_sect_map(f"{target_path}/sectmap.txt")
    print(addresses)

    if (os.system(f"cd {target_path}/build & {hooks_compiler} -c {HOOKS_FLAGS} ../hooks/*.cpp")):
        raise Exception("Errors occured during building of hooks files")

    hooks: list[COFFData] = []
    for path in list_files_at(f"{target_path}/build", "**/*.o"):
        coff_data = COFFData(f"{target_path}/build/{path}", f"build/{path}")
        for sect in coff_data.sects:
            if len(sect.name) >= 8:
                raise Exception(f"sect name too long {sect.name}")
            if sect.size == 0:
                raise Exception(f"sect size is invalid")
            if sect.offset < base_pe.imgbase:
                raise Exception(
                    f"sect offset is larger than image base: {sect.offset:x}, base {base_pe.imgbase:x}")
        hooks.append(coff_data)

    section_pe = PEData(f"{target_path}/build/section.pe")
    ssize = section_pe.sects[-1].v_offset + \
        section_pe.sects[-1].v_size + section_pe.sects[0].v_offset
    print(ssize)

    with open(f"{target_path}/patch.ld", "w") as pld:
        pld.writelines(["OUTPUT_FORMAT(pei-i386)\n",
                        "OUTPUT(build/patch.pe)\n",
                        ])

        for name, address in addresses.items():
            pld.write(f"\"{name}\" = {address};\n")

        pld.writelines(["SECTIONS {\n"
                        ])
        hi = 0
        for hook in hooks:
            for sect in hook.sects:
                pld.writelines([
                    f" .h{hi} 0x{sect.offset:x} : SUBALIGN(1) {{\n",
                    f"     {hook.name}({sect.name})\n",
                    " }\n",
                ])
                hi += 1
        pld.writelines([f"  .exxt 0x{base_pe.imgbase + new_v_offset:x}: {{\n",
                        f"  . = . + {ssize};\n",
                        "    *(.data)\n    *(.bss)\n    *(.rdata)\n  }\n",
                        "  /DISCARD/ : {\n    *(.text)\n    *(.text.startup)\n",
                        "    *(.rdata$zzz)\n    *(.eh_frame)\n    *(.ctors)\n    *(.reloc)\n  }\n}"
                        ])
    print(os.system(
        f"cd {target_path} & {linker_path} -T patch.ld --image-base {base_pe.imgbase} -s -Map build/patchmap.txt"))

    base_file_data = base_pe.data

    def replace_data(new_data, offset):
        nonlocal base_file_data
        base_file_data = base_file_data[:offset] + \
            new_data + base_file_data[offset+len(new_data):]

    patch_pe = PEData(f"{target_path}/build/patch.pe")
    hi = 0
    for hook in hooks:
        if len(hook.sects) == 0:
            print(f"No hooks in {hook.name}")
        for sect in hook.sects:
            psect = patch_pe.find_sect(f".h{hi}")
            size = sect.size
            replace_data(
                patch_pe.data[psect.f_offset:psect.f_offset + size], psect.v_offset)
            hi += 1

    exxt_sect = patch_pe.find_sect(".exxt")
    nsect = PESect(exxt_sect.name,
                   exxt_sect.v_size,
                   new_v_offset,
                   exxt_sect.f_size,
                   new_f_offset,
                   0xE0000060
                   )
    base_pe.sects.append(nsect)
    if SECT_SIZE > 0:
        if SECT_SIZE < exxt_sect.f_size:
            raise Exception(
                f"Section size too small. Required: 0x{exxt_sect.f_size:x}")

        exxt_sect.v_size = SECT_SIZE
        exxt_sect.f_size = SECT_SIZE

    replace_data(
        patch_pe.data[exxt_sect.f_offset:exxt_sect.f_offset + exxt_sect.f_size], nsect.v_offset)

    for s in section_pe.sects:
        replace_data(section_pe.data[s.f_offset:s.f_offset+s.f_size],
                     nsect.f_offset+s.v_offset-section_pe.sects[0].v_offset)

    def save_new_base_data(data):
        with open(f"{target_path}/ForgedAlliance_exxt.exe", "wb") as nf:
            sect_count = len(base_pe.sects)
            nf.write(base_file_data)
            nf.seek(base_pe.offset+0x6)
            nf.write(struct.pack("H", sect_count))
            img_size = base_pe.sects[-1].v_offset + base_pe.sects[-1].v_size

            nf.seek(base_pe.offset+0x50)
            nf.write(struct.pack("I", img_size))

            nf.seek(base_pe.offset+0xf8)
            for sect in base_pe.sects:
                nf.write(sect.to_bytes())

    save_new_base_data(base_file_data)


if __name__ == "__main__":
    main(*sys.argv)
    # FILE_PATH = "F:\GIT\SCFA-python-patcher\FA-Binary-Patches-SIMPLE\ForgedAlliance_base.exe"
    # pe = PEData(FILE_PATH)
    # print(pe.sects)
    # coff = COFFData(
    #     r"F:\GIT\SCFA-python-patcher\FA-Binary-Patches-SIMPLE\build\SetStatFix.o")
