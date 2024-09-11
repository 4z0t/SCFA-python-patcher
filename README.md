# About

This repo is about python implementation of SCFA executable patcher.
It uses both clang and gcc compilers to combine advantages of both compilers.

# Run

To apply patcher on patch files run this command:

`python main.py [path to folder with patches] [path to clang++ executable] [path to linker executable (ld)] [path to g++ executable]`

## Patches folder structure

- **/build**: Here happens build for all source files. Patcher leaves address maps after build for debug purposes.
- **/include**: Header files.
- **/section**: All files with patches that involve logic written with C/C++. 
  - `*.cpp` files are built with *g++*
  - `*.cxx` files are built with *clang++*
  - Can contain nested folders
  - Can contain header files
- **/hooks**: All files with asm that is injected by specified addresses. 
- ***define.h***: Generated file for hooks to use.
- ***SigPatches.txt***: File with signature patches. Replaces one binary sequence with another. Applied after build.
- ***ForgedAlliance_base.exe***: Base executable of the game for patching.
- ***ForgedAlliance_exxt.exe***: Result executable, run with [debugger](https://github.com/FAForever/FADeepProbe) for more information in case of crashes.

## Versions

Versions of compilers and linkers used.

clang++ compiler: 
* version 18.1.8
* Target: x86_64-pc-windows-msvc
* Thread model: posix

ld linker:
* GNU ld (GNU Binutils) 2.40

g++ compiler:
* g++ (Rev6, Built by MSYS2 project) 13.1.0

python:
* 3.12.4

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
    output:  char* Moho::DRAW_Rect (
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