import os
from typing import Any

import pytest
from pytest import FixtureRequest

from dir_analyzer import FiletypeInfoStorage, main

LOCALDIR_PATH = os.path.dirname(os.path.realpath(__file__))

TESTED_TYPES = [
    ("Image", 1, 9333),
    ("Text", 1, 16),
    ("Video", 1, 9100820),
    ("Audio", 1, 4240275),
    ("Application", 1, 13254713),
]

@pytest.fixture(scope="module")
def analysis_output() -> dict[str, dict[str, FiletypeInfoStorage] | FiletypeInfoStorage | int]:
    return main(os.path.join(LOCALDIR_PATH, "data"))

def test_result_storages_in_output(analysis_output: dict[str, Any]):
    assert "result_storages" in analysis_output


@pytest.mark.parametrize("storage_name", [entry[0] for entry in TESTED_TYPES])
def test_fixture_output(analysis_output: dict[str, Any], storage_name: str):
    assert storage_name in analysis_output["result_storages"]
    storage = analysis_output["result_storages"][storage_name]
    assert isinstance(storage, FiletypeInfoStorage)


@pytest.fixture(scope="module")
def fileinfostorage(analysis_output: dict[str, Any], request: FixtureRequest):
    return analysis_output["result_storages"][request.param]


@pytest.mark.parametrize("fileinfostorage,expected_found,expected_size", TESTED_TYPES, indirect=["fileinfostorage"])
def test_findings(
        fileinfostorage: FiletypeInfoStorage,
        expected_size: int,
        expected_found: int) -> None:
    assert fileinfostorage.found_files == expected_found
    assert fileinfostorage.found_size == expected_size
