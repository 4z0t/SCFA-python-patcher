# About

This repo is about python implementation of SCFA executable patcher.
It uses both clang and gcc compilers to combine advantages of both compilers.

# Run

To apply patcher on patch files run this command:

`python main.py [path to folder with patches] [path to clang++ executable] [path to linker executable (ld)] [path to g++ executable]`

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

