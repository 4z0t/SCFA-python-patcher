# Python

To patch an exe you with Python patcher you obviously need Python interpreter.
Install newest version [here](https://www.python.org/downloads/).

# Compilers

You will need GCC and Clang compilers. 
Clang compiler installation:
* Goto [github releases of llvm](https://github.com/llvm/llvm-project/releases/tag/llvmorg-18.1.8)
* Download **LLVM-18.1.8-win64.exe**
* Install

GCC compiler installation:
* Install [MSYS2](https://www.msys2.org/)
* Install GCC x32/x64 via MSYS console:
    * x32: pacman -S mingw-w64-i686-gcc
    * x64: pacman -S mingw-w64-x86_64-gcc

# IDE

For creating of patches **Visual Studio Code** is used with `ms-vscode.cpptools` extension, which can be installed with Extensions tab.
In preferences set default C++ formatter to `ms-vscode.cpptools`.

