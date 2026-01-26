import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    target_folder_path: Path
    build_folder_path: Path
    inout_name: Path = "ForgedAlliance_base.exe"
    output_name: Path = "ForgedAlliance_exxt.exe"

    clang_path: Path = "clang++"
    gcc_path: Path = "g++"
    linker_path: Path = "ld"

    clang_flags: tuple[str] = ()
    gcc_flags: tuple[str] = ()
    asm_flags: tuple[str] = ()

    functions : dict[str, str] = {}

    @classmethod
    def load_from_json(cls, path: Path) -> Config:
        pass

    def __post_init__(self):
        self.build_folder_path = self.build_folder_path or (
            self.target_folder_path / "build"
        )
