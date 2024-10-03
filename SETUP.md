# Python

To patch an exe you with Python patcher you obviously need Python interpreter.
Install newest version [here](https://www.python.org/downloads/).

# Compilers

You will need GCC and Clang compilers. 

Clang compiler installation:
* Goto [github releases of llvm](https://github.com/llvm/llvm-project/releases/tag/llvmorg-18.1.8)
* Download **clang+llvm-18.1.8-x86_64-pc-windows-msvc.tar.xz**
* Unpack into preferred location
* You need `/bin/clang++.exe`

GCC compiler installation:
* Install [MSYS2](https://www.msys2.org/)
* Install GCC x32/x64 via MSYS console:
    * x32: pacman -S mingw-w64-i686-gcc
    * x64: pacman -S mingw-w64-x86_64-gcc
* You need `/mingw32/bin/g++.exe` and `/mingw32/bin/ld.exe`

After everything installed you need to clone patches repo (right now only 4z0t's fork is compatible).

Now you can setup build script:
```bat
python main.py [Path to patches folder] [Path to clang++.exe] [Path to ld.exe] [Path to g++.exe]
```
After you successfully build, you have to test what you've got somehow.
You have 2 options:
* Running patched game with files from FAF client gamedata
* Running patched game with files from repo


# IDE

For creating of patches **Visual Studio Code** is used with `ms-vscode.cpptools` extension, which can be installed with Extensions tab.
In preferences set default C++ formatter to `ms-vscode.cpptools`.

# Decompiler

TODO