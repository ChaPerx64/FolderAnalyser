import os
from typing import Any

import pytest

from dir_analyzer import FiletypeInfoStorage, main

LOCALDIR_PATH = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture(scope="package")
def analysis_output() -> dict[str, list[FiletypeInfoStorage] | FiletypeInfoStorage | int]:
    return main(os.path.join(LOCALDIR_PATH, "data"))
