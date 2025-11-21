from pathlib import Path

__MAIN_DATA_FOLDER = Path.cwd()

def set_main_data_folder(path: Path):
    print(path)
    global __MAIN_DATA_FOLDER
    __MAIN_DATA_FOLDER = path

def get_main_data_folder() -> Path:
    return __MAIN_DATA_FOLDER