import re
from pathlib import Path
import Patcher


class Section:
    ...


class Hook:
    ...


def generate_hook_cpp(file_path_s: str):
    file_path = Path(file_path_s)


def scan_hooks(folder_path_s: str):
    folder_path = Path(folder_path_s)
    print(Patcher.list_files_at(folder_path, "*.hook"))


scan_hooks("F:\\GIT\\SCFA-python-patcher\\FA-Binary-Patches\\hooks\\")
