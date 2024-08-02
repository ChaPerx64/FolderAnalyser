import os
from typing import Any

import pytest
from pytest import FixtureRequest

from dir_analyzer import FiletypeInfoStorage, main

LOCALDIR_PATH = os.path.dirname(os.path.realpath(__file__))

TESTED_TYPES = [
    ("Image", 1, 9333),
    ("Text", 2, 31),
    ("Video", 1, 9100820),
    ("Audio", 1, 4240275),
    ("Application", 1, 13254713),
]


@pytest.fixture(scope="module")
def analysis_output() -> dict[str, dict[str, FiletypeInfoStorage] | FiletypeInfoStorage | int | list[str]]:
    return main(os.path.join(LOCALDIR_PATH, "data"), thorough=True)


def test_result_storages_in_output(analysis_output: dict[str, Any]):
    assert "result_storages" in analysis_output


@pytest.mark.parametrize("storage_name", [entry[0] for entry in TESTED_TYPES])
def test_results_storage(analysis_output: dict[str, Any], storage_name: str):
    assert storage_name in analysis_output["result_storages"]
    storage = analysis_output["result_storages"][storage_name]
    assert isinstance(storage, FiletypeInfoStorage)


def test_others_storage(analysis_output: dict[str, Any]):
    assert "others_storage" in analysis_output
    assert isinstance(analysis_output["others_storage"], FiletypeInfoStorage)


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


def test_others_found(analysis_output: dict[str, Any]):
    assert analysis_output["others_storage"].found_files == 0
    assert analysis_output["others_storage"].found_size == 0


def test_error_count(analysis_output: dict[str, Any]):
    assert analysis_output["errored_files_count"] == 0
