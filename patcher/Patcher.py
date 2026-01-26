from .PEData import PEData, PESect
from .COFFData import COFFData, COFFSect
import os
from pathlib import Path
import re
import json
from typing import Optional
import struct
import itertools
from patcher import Hook
from .Config import Config


SECT_SIZE = 0x80000

ASM_RE = re.compile(r"(asm\(\"(0[xX][0-9a-fA-F]{1,8})\"\);)", re.IGNORECASE)
CALL_RE = re.compile(
    r"((call|jmp|je|jne)\s+(0[xX][0-9a-fA-F]{1,8}))", re.IGNORECASE)
SPACES_RE = re.compile(" +")


def scan_header_files(target_path: Path) -> list[str]:
    functions_addresses = []
    contents = itertools.chain.from_iterable(read_files_contents(
        target_path, list_files_at(target_path, "**/*.h")).values())

    for line in contents:
        matches = ASM_RE.finditer(line)
        for match in matches:
            functions_addresses.append(match.group(2))  # get address
    return functions_addresses


def list_files_at(folder: Path, pattern: str, excluded: Optional[list[str]] = None) -> list[str]:
    pathlist = folder.glob(pattern)
    paths = [str(path.relative_to(folder)) for path in pathlist]

    if excluded is not None:
        paths = [path for path in paths if path not in excluded]
    return paths


def find_patch_files(folder_path: Path) -> list[str]:
    return list_files_at(folder_path, "**/*.cpp", ["main.cpp"])


def read_files_contents(dir_path: Path, paths: list[str]) -> dict[str, list[str]]:
    files_contents: dict[str, list[str]] = {}
    for path in paths:
        files_contents[path] = []
        file_contents = files_contents[path]
        with open(dir_path / path, "r")as f:
            file_contents.extend(f.readlines())
            file_contents.append("\n")

    return files_contents


def preprocess_lines(files_contents: dict[str, list[str]]) -> tuple[list[str], dict[str, str]]:
    new_lines = []
    address_names = {}
    for file_name, contents in files_contents.items():
        file_lines = []
        file_addresses = {}
        for line in contents:
            matches = CALL_RE.finditer(line)
            new_line = line
            for match in matches:
                full_s = match.group(0)
                address = match.group(3)
                address_name = "_" + address[1::]
                s_start, s_end = match.span()
                file_addresses[address_name] = address
                new_line = new_line[:s_start] + \
                    full_s.replace(address, address_name) + new_line[s_end:]
            file_lines.append(new_line)
        if len(file_addresses) == 0:
            new_lines.append(f"#include \"{file_name}\"\n")
        else:
            new_lines.extend(file_lines)
            address_names |= file_addresses
    return new_lines, address_names


def create_sections_file(path: Path, address_map: dict[str, str]):

    HEADER = """
OUTPUT_FORMAT(pei-i386)
OUTPUT(section.pe)
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
        .clang : {
            clangfile.o
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
        for name, address in address_map.items():
            f.write(f"\"{name}\" = {address};\n")
        f.write(SECTIONS)


def create_cxx_sections_file(path, address_map):
    with open(path, "w") as f:
        for name, address in address_map.items():
            f.write(f"\"{name}\" = {address};\n")


def parse_sect_map(file_path: Path) -> dict[str, str]:
    addresses: dict[str, str] = {}
    with open(file_path, "r") as f:
        line = f.readline()
        while not line.startswith(" *(.text*)"):
            line = f.readline()

        line = f.readline()
        while not line.startswith(" *(.data*)"):
            items = SPACES_RE.sub(" ", line.strip()).split("(")[0].split(" ")
            if len(items) != 2 or items[1].startswith("?"):
                line = f.readline()
                continue

            address, name = items

            if name in addresses:
                raise Exception(
                    f"Duplicated name for patch function {name}")

            addresses[name] = address

            line = f.readline()

        line = f.readline()
        while not line.startswith(" *(.bss*)"):
            items = SPACES_RE.sub(" ", line.strip()).split(" ")
            if len(items) != 2 or items[1].startswith("?"):
                line = f.readline()
                continue

            address, name = items

            if name in addresses:
                raise Exception(
                    f"Duplicated name for patch function {name}")

            addresses[name] = address

            line = f.readline()

        line = f.readline()
        while not line.startswith(" *(.rdata)"):
            items = SPACES_RE.sub(" ", line.strip()).split(" ")
            if len(items) != 2 or items[1].startswith("?"):
                line = f.readline()
                continue

            address, name = items

            if name in addresses:
                raise Exception(
                    f"Duplicated name for patch function {name}")

            addresses[name] = address

            line = f.readline()

    addresses = {name.split('@')[0]: address for name,
                 address in addresses.items()}
    addresses = {name: address for name,
                 address in addresses.items() if name}
    return addresses


def remove_files_at(folder: Path, pattern: str):
    pathlist = folder.glob(pattern)
    for p in pathlist:
        p.unlink()


def apply_sig_patches(file_path: Path, data: bytearray):
    sig_patches = []
    with open(file_path, "r") as sig_f:

        for line in sig_f.readlines():
            if line.startswith("//") or line in ("", "\n"):
                continue

            sig_patches.append(line.replace(" ", "").replace("\n", ""))
    signatures = []
    for i in range(0, len(sig_patches), 2):
        pattern = sig_patches[i]
        replacement = sig_patches[i+1]
        if len(pattern) < len(replacement):
            raise Exception(
                f"Replacement sig patch must be shorter than pattern: {pattern} and {replacement}")

        signature = []
        any_len = 0
        seq = ""
        for i in range(0, len(pattern), 2):
            item = pattern[i:i+2:]
            if item == "??":
                if len(seq) != 0:
                    signature.append(seq)
                    seq = ""
                any_len += 1

            else:
                if any_len != 0:
                    signature.append(any_len)
                    any_len = 0
                seq += item
        if len(seq) != 0:
            signature.append(seq)
        elif any_len != 0:
            signature.append(any_len)
        signatures.append((signature, replacement))

    bin_sigs = []
    for sig, replacement in signatures:
        bin_sig = []
        for item in sig:
            if isinstance(item, str):
                bin_sig.append(bytes.fromhex(item))
            else:
                bin_sig.append(item)
        bin_sigs.append((bin_sig, bytes.fromhex(replacement)))

    def yield_sig_locations(data: bytearray, sig: list[bytes | int]):
        start_location = 0
        first_bytes, *tail = sig
        while start_location != -1:
            start_location = data.find(first_bytes, start_location)
            if start_location == -1:
                break
            search_location = start_location + len(first_bytes)

            for item in tail:
                if isinstance(item, bytes):
                    if data[search_location:search_location+len(item)] != item:
                        break
                    search_location += len(item)
                else:
                    search_location += item
            else:
                yield start_location
                start_location = search_location
                continue
            start_location += len(first_bytes)

    i = 0
    for sig, replacement in bin_sigs:
        locations = [pos for pos in yield_sig_locations(data, sig)]
        for pos in locations:
            data[pos:pos+len(replacement)] = replacement
        print(sig_patches[i])
        print(f"applied {len(locations)} times")
        i += 2


def scan_for_headers_in_section(sections_path: Path):
    paths = (Path(s) for s in list_files_at(sections_path, "**/*.h"))
    folders = {str(path.parent) for path in paths}
    return folders


def run_system(command: str) -> int:
    print(command)
    return os.system(command.replace("\n", " "))


def patch(config_path):
    config = Config.load_from_json(Path(config_path))
    print(config)

    base_pe = PEData(config.input_path)
    new_v_offset = 0
    new_f_offset = 0

    for sect in base_pe.sects:
        new_v_offset = max(sect.v_offset + sect.v_size, new_v_offset)
        new_f_offset = max(sect.f_offset + sect.f_size, new_f_offset)

    def align(v, a):
        return (v + a-1) & (~(a-1))

    new_v_offset = align(new_v_offset, base_pe.sectalign)
    new_f_offset = align(new_f_offset, base_pe.filealign)
    print(f"Image base: {base_pe.imgbase + new_v_offset - 0x1000:x}")

    section_folder_path = config.target_folder_path / "section"

    paths = find_patch_files(section_folder_path)

    # files_contents = read_files_contents(f"{target_path}/section/", paths)
    # files_contents, address_names = preprocess_lines(files_contents)

    with open(section_folder_path / "main.cpp", "w") as main_file:
        for path in paths:
            main_file.writelines(f"#include \"{path}\"\n")
        # main_file.writelines(files_contents)

    function_addresses = {
        name: name for name in scan_header_files(config.target_folder_path)}

    cxx_files_contents = read_files_contents(section_folder_path, list_files_at(
        section_folder_path, "**/*.cxx", ["main.cxx"]))
    cxx_files_contents, cxx_address_names = preprocess_lines(
        cxx_files_contents)

    with open(section_folder_path / "main.cxx", "w") as main_file:
        main_file.writelines(cxx_files_contents)

    folders = scan_for_headers_in_section(section_folder_path)
    includes = " ".join((f"-I ../section/{folder}/" for folder in folders))

    # if run_system(
    #         f"""cd {build_folder_path} &
    #         {clang_compiler_path} -M
    #         -I ../include/ {includes}
    #         ../section/main.cxx"""):
    #     raise Exception("Errors occurred during building of cxx files")
    build_folder_path = config.build_folder_path

    if run_system(
            f"""cd {build_folder_path} &
            {config.clang_path} -c {" ".join(config.clang_flags)}
            -I ../include/ {includes}
            ../section/main.cxx -o clangfile.o"""):
        raise Exception("Errors occurred during building of cxx files")

    create_sections_file(config.target_folder_path / "section.ld",
                         function_addresses | cxx_address_names | config.functions)
    if run_system(
            f"""cd {build_folder_path} &
            {config.gcc_path} {" ".join(config.gcc_flags)}
            -I ../include/ {includes}
            -Wl,-T,../section.ld,--image-base,{base_pe.imgbase + new_v_offset - 0x1000},-s,-Map,sectmap.txt,-o,section.pe
            ../section/main.cpp"""):
        raise Exception("Errors occurred during building of patch files")

    remove_files_at(build_folder_path, "**/*.o")

    addresses = parse_sect_map(build_folder_path / "sectmap.txt")

    def create_defines_file(path: Path, addresses: dict[str, str]):
        with open(path, "w") as f:
            f.writelines([
                "#define QUAUX(X) #X\n",
                "#define QU(X) QUAUX(X)\n\n"
            ])
            for name, address in addresses.items():
                f.write(f"#define {name} {address}\n")
    create_defines_file(config.target_folder_path / "define.h", addresses)

    def generate_hook_files(folder_path: Path):
        for file_path in list_files_at(folder_path, "**/*.hook"):
            hook = Hook. load_hook(folder_path/file_path)
            hook_path = file_path.replace(os.sep, "_") + ".cpp"
            print(f"Generating {hook_path}")
            with open(folder_path/hook_path, "w") as f:
                f.write(hook.to_cpp())

    generate_hook_files(config.target_folder_path/"hooks")

    if run_system(
            f"""cd {build_folder_path} &
            {config.gcc_path} -c {" ".join(config.asm_flags)} ../hooks/*.cpp"""):
        raise Exception("Errors occurred during building of hooks files")

    hooks: list[COFFData] = []
    for path in list_files_at(build_folder_path, "**/*.o"):
        coff_data = COFFData(build_folder_path / path, f"build/{path}")
        for sect in coff_data.sects:
            if len(sect.name) >= 8:
                raise Exception(f"sect name too long {sect.name}")
            if sect.size == 0:
                raise Exception(f"sect size is invalid")
            if sect.offset < base_pe.imgbase:
                raise Exception(
                    f"sect offset is larger than image base: {sect.offset:x}, base {base_pe.imgbase:x}")
        hooks.append(coff_data)

    section_pe = PEData(build_folder_path / "section.pe")
    ssize = section_pe.sects[-1].v_offset + \
        section_pe.sects[-1].v_size + section_pe.sects[0].v_offset

    with open(config.target_folder_path / "patch.ld", "w") as pld:
        pld.writelines([
            "OUTPUT_FORMAT(pei-i386)\n",
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
                    f" .h{hi:X} 0x{sect.offset:x} : SUBALIGN(1) {{\n",
                    f"     {hook.name}({sect.name})\n",
                    " }\n",
                ])
                hi += 1
        pld.writelines([
            f"  .exxt 0x{base_pe.imgbase + new_v_offset:x}: {{\n",
            f"  . = . + {ssize};\n",
            "    *(.data)\n",
            "    *(.bss)\n",
            "    *(.rdata)\n",
            "  }\n",
            "  /DISCARD/ : {\n",
            "    *(.text)\n",
            "    *(.text.startup)\n",
            "    *(.rdata$zzz)\n",
            "    *(.eh_frame)\n",
            "    *(.ctors)\n",
            "    *(.reloc)\n",
            "  }\n",
            "}"
        ])

    # if run_system(
    #     f"""cd {target_path} &
    #     {clang_compiler_path} -pipe -m32 -Os -nostdlib -Werror -masm=intel -std=c++20 -march=core2 -c
    #         -I ../include/ {includes}
    #         ../section/test.cxx -o test.o
    #     """
    # ):
    #     raise Exception("Errors occurred during builing of test")

    if run_system(
            f"""cd {config.target_folder_path} &
            {config.linker_path} -T patch.ld --image-base {base_pe.imgbase} -s -Map build/patchmap.txt"""):
        raise Exception("Errors occurred during linking")

    base_file_data = bytearray(base_pe.data)

    def replace_data(new_data, offset):
        nonlocal base_file_data
        base_file_data[offset:offset+len(new_data)] = new_data

    patch_pe = PEData(build_folder_path / "patch.pe")
    hi = 0
    for hook in hooks:
        if len(hook.sects) == 0:
            print(f"No hooks in {hook.name}")
            continue
        for sect in hook.sects:
            psect = patch_pe.find_sect(f".h{hi:X}")
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
                f"Section size too small. Required: 0x{exxt_sect.f_size: x}")

        exxt_sect.v_size = SECT_SIZE
        exxt_sect.f_size = SECT_SIZE

    replace_data(
        patch_pe.data[exxt_sect.f_offset:exxt_sect.f_offset + exxt_sect.f_size], nsect.v_offset)

    for s in section_pe.sects:
        replace_data(section_pe.data[s.f_offset:s.f_offset+s.f_size],
                     nsect.f_offset+s.v_offset-section_pe.sects[0].v_offset)

    apply_sig_patches(config.target_folder_path /
                      "SigPatches.txt", base_file_data)

    def save_new_base_data(data: bytearray):
        with open(config.output_path, "wb") as nf:
            sect_count = len(base_pe.sects)
            nf.write(data)
            nf.seek(base_pe.offset+0x6)
            nf.write(struct.pack("H", sect_count))
            img_size = base_pe.sects[-1].v_offset + base_pe.sects[-1].v_size

            nf.seek(base_pe.offset+0x50)
            nf.write(struct.pack("I", img_size))

            nf.seek(base_pe.offset+0xf8)
            for sect in base_pe.sects:
                nf.write(sect.to_bytes())

    save_new_base_data(base_file_data)

    remove_files_at(build_folder_path, "**/*.o")
    remove_files_at(config.target_folder_path / "hooks", "*.hook.cpp")
