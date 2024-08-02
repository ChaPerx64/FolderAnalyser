import os
from pathlib import Path
from typing import Any, Generator

import pytest

from dir_analyzer import FiletypeInfoStorage, main

TEMPORARY_DIR_PATH = Path(os.path.dirname(
    os.path.realpath(__file__))) / 'permissions_temp'


@pytest.fixture(scope="package")
def create_files() -> Generator[Path, Any, None]:
    TEMPORARY_DIR_PATH.mkdir(exist_ok=True)

    world_writable = TEMPORARY_DIR_PATH / 'world_writable.txt'
    world_writable.touch()
    world_writable.chmod(0o666)

    suid_file = TEMPORARY_DIR_PATH / 'suid_file.bin'
    suid_file.touch()
    suid_file.chmod(0o4755)

    sgid_file = TEMPORARY_DIR_PATH / 'sgid_file.bin'
    sgid_file.touch()
    sgid_file.chmod(0o2755)

    yield TEMPORARY_DIR_PATH

    world_writable.unlink()
    suid_file.unlink()
    sgid_file.unlink()
    TEMPORARY_DIR_PATH.rmdir()


@pytest.fixture(scope="package")
def analysis_output(create_files: Path) -> dict[str, dict[str, FiletypeInfoStorage] | FiletypeInfoStorage | int | list[str]]:
    return main(str(TEMPORARY_DIR_PATH), use_default_config=True)
