import pytest
from dir_analyzer import FiletypeInfoStorage


def test_analysis_output(
        analysis_output: dict[str, dict[str, FiletypeInfoStorage]
                              | FiletypeInfoStorage | int | list[str]]
):
    assert "permission_warnings" in analysis_output
    assert isinstance(analysis_output["permission_warnings"], list)


@pytest.fixture
def permission_warnings(
        analysis_output: dict[str, dict[str, FiletypeInfoStorage]
                              | FiletypeInfoStorage | int | list[str]]
) -> list[str]:
    return analysis_output["permission_warnings"]

def test_permissions(
        permission_warnings: list[str]
):
    assert len(permission_warnings) == 3
    
