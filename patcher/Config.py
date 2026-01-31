import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Self


@dataclass
class Config:
    path: Path
    target_folder_path: Path
    build_folder_path: Path
    input_name: str = "ForgedAlliance_base.exe"
    output_name: str = "ForgedAlliance_exxt.exe"

    clang_path: Path = "clang++"
    gcc_path: Path = "g++"
    linker_path: Path = "ld"

    clang_flags: tuple[str] = ()
    gcc_flags: tuple[str] = ()
    asm_flags: tuple[str] = ()

    @classmethod
    def load_from_json(cls, path: Path) -> Self:
        path = Path(path).resolve()
        with open(path, 'r') as f:
            config = json.load(f)

        return cls(
            path=path,
            target_folder_path=config.get("target_folder_path", path.parent),
            build_folder_path=config.get("build_folder_path"),
            input_name=config.get("input_name", Config.input_name),
            output_name=config.get("output_name", Config.output_name),
            clang_path=config.get("clang", Config.clang_path),
            gcc_path=config.get("gcc", Config.gcc_path),
            linker_path=config.get("linker", Config.linker_path),
            clang_flags=config.get("clang_flags", Config.clang_flags),
            gcc_flags=config.get("gcc_flags", Config.gcc_flags),
            asm_flags=config.get("asm_flags", Config.asm_flags),
        )

    def __post_init__(self):
        self.target_folder_path = Path(self.target_folder_path)

        if not self.target_folder_path.is_absolute():
            self.target_folder_path = self.path.parent / self.target_folder_path

        self.build_folder_path = Path(self.build_folder_path)\
            if self.build_folder_path \
            else self.target_folder_path / "build"

        self.clang_path = Path(self.clang_path)
        self.gcc_path = Path(self.gcc_path)
        self.linker_path = Path(self.linker_path)

        if not self.build_folder_path.is_absolute():
            raise ValueError(
                "build_folder_path must be an absolute path to folder")

    @property
    def input_path(self) -> Path:
        return self.target_folder_path / self.input_name

    @property
    def output_path(self) -> Path:
        return self.build_folder_path / self.output_name
