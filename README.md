# About

This repo is about python implementation of SCFA executable patcher.
It uses both clang and gcc compilers to combine advantages of both compilers.

# Setup

See [SETUP.md](./SETUP.md).

# Run

To apply patcher on patch files run this command:

`python main.py [path to config file]`

config structure:
```json
{
    // path to target folder. Can be either relative or absolute.
    // if relative path then it will be {config path}/{target_folder_path}
    "target_folder_path": "FA-Binary-Patches",
    // path to build folder. Defaults to "{target_folder_path}/build"
    "build_folder_path": null,
    // names of input and output files
    "input_name": "ForgedAlliance_base.exe",
    "output_name": "ForgedAlliance_exxt.exe",
    // path to clang++ compiler. Defaults to "clang++"
    "clang": "clang++.exe",
    // path to g++ compiler. Defaults to "g++"
    "gcc": "g++.exe",
    // path to linker. Defaults to "ld"
    "linker": "ld.exe",
    // flags for compilers
    "clang_flags": [
        "-pipe",
        "-m32",
        "-O3",
        "-nostdlib",
        "-Werror",
        "-masm=intel",
        "-std=c++20",
        "-march=core2"
    ],
    "gcc_flags": [
        "-pipe",
        "-m32",
        "-Os",
        "-fno-exceptions",
        "-nostdlib",
        "-nostartfiles",
        "-fpermissive",
        "-masm=intel",
        "-std=c++20",
        "-march=core2",
        "-mfpmath=both"
    ],
    "asm_flags": [
        "-pipe",
        "-m32",
        "-Os",
        "-fno-exceptions",
        "-nostdlib",
        "-nostartfiles",
        "-w",
        "-fpermissive",
        "-masm=intel",
        "-std=c++20",
        "-march=core2",
        "-mfpmath=both"
    ],
}
```

## Patches folder structure

- **/build**: Here happens build for all source files. Patcher leaves address maps after build for debug purposes.
- **/hooks**: All files with asm that is injected by specified addresses. 
- **/include**: Header files.
- **/section**: All files with patches that involve logic written with C/C++. 
  - `*.cpp` files are built with *g++*
  - `*.cxx` files are built with *clang++*
  - Can contain nested folders
  - Can contain header files
  - Can contain `.hook` files
- ***config.json***: Config file for patcher.
- ***section.ld***: Main linker script.
- ***SigPatches.txt***: File with signature patches. Replaces one binary sequence with another. Applied after build.
- ***ForgedAlliance_base.exe***: Base executable of the game for patching.
- ***ForgedAlliance_exxt.exe***: Result executable, run with [debugger](https://github.com/FAForever/FADeepProbe) for more information in case of crashes.

## Versions

Versions of compilers and linkers used.

clang++ compiler: 
* clang version 21.1.0
* Target: x86_64-pc-windows-msvc
* Thread model: posix

ld linker:
* GNU ld (GNU Binutils) 2.39

g++ compiler:
* g++ (i686-posix-dwarf-rev0, Built by MinGW-Builds project) 13.2.0      

python:
* 3.14.2

# HumanUserCalls.py

A small script to convert x86 usercall/purge functions from IDA pseudo code into C ones made of GCC inline asm.
Still suggested to check generated code as well as performing additional changes for asm.

## Example

Input:
```cpp
    char *__usercall Moho::DRAW_Rect@<eax>(
                          Vector3f *vec1@<eax>,
                          Vector3f *vec2@<ecx>,
                          int color@<edi>,
                          float thickness@<xmm0>,
                          CD3DPrimBatcher *batcher,
                          Vector3f *vec3,
                          CHeightField *heightField,
                          float a8)
```
Output:
```cpp
    char* Moho::DRAW_Rect (
                Vector3f* vec1,
                Vector3f* vec2,
                int color,
                float thickness,
                CD3DPrimBatcher* batcher,
                Vector3f* vec3,
                CHeightField* heightField,
                float a8)
            {
            char* __result;
            asm(
                "push %[a8];"       
                "push %[heightField];"
                "push %[vec3];"
                "push %[batcher];"
                "movss xmm0, %[thickness];"
                "call ADDRESS;"
                "add esp, 0x10;"
                : "=a" (__result)
                : [vec1] "a" (vec1), [vec2] "c" (vec2), [color] "D" (color), [thickness] "m" (thickness), [batcher] "g" (batcher), [vec3] "g" (vec3), [heightField] "g" (heightField), [a8] "g" (a8)
                :"xmm0"
            );
            return __result;
            }
```

# Debug.py

A script to debug game executable. Extracts from log crash data and uses build data to tell more information.

`python Debug.py [Path to patches folder] [Command line arguments to run the game]`

Example:

```
python ./Debug.py F:\GIT\FA-Binary-Patches ^
            C:\ProgramData\FAForever\bin\FAFDebugger.exe ^
            C:\ProgramData\FAForever\bin\ForgedAlliance_exxt.exe /init init-dev.lua /nobugreport /log C:\ProgramData\FAForever\bin\logs\game.log ^
            /EnableDiskWatch /showlog
```