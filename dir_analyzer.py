import mimetypes
import os
import stat
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any
import json

import magic
import typer
from humanize import naturalsize
from rich import print as rich_print
from rich.console import Console
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeRemainingColumn, TaskID)
from rich.table import Column, Table


CONFIG_PATH = "./config.json"
BIGFILES_OUTPUT_PATH = "./bigfiles.txt"
PERMISSIONS_OUTPUT_PATH = "./permissions.txt"

DEFAULT_CONFIG = {
    "searchable_types": {
        "Image": {
            "tag": "image/",
        },
        "Text": {
            "tag": "text/",
        },
        "Audio": {
            "tag": "audio/",
        },
        "Video": {
            "tag": "video/",
        },
        "Application": {
            "tag": "application/",
        },
    }
}


def get_config() -> Any:
    """
    Load the configuration from the CONFIG_PATH file.
    If the file doesn't exist, create it with DEFAULT_CONFIG.

    Returns:
        Any: The loaded configuration as a JSON object.
    """
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


@dataclass
class FiletypeInfoStorage:
    tag: str
    found_files = 0
    found_size = 0
    displayable_name: str
    found_files_paths: list[str] = field(default_factory=list)


def check_path(path: str) -> None:
    """
    Verify if the given path exists and is a directory.

    Args:
        path (str): The path to check.

    Raises:
        typer.Exit: If the path doesn't exist or is not a directory.
    """
    if not os.path.exists(path):
        typer.secho("Incorrect path - does not exist", fg=typer.colors.RED)
        raise typer.Exit()
    if not os.path.isdir(path):
        typer.secho("Incorrect path - should be a directory",
                    fg=typer.colors.RED)
        raise typer.Exit()


def check_size_threshold(size_threshold: float) -> None:
    """
    Verify if the given size threshold is non-negative.

    Args:
        size_threshold (float): The size threshold to check.

    Raises:
        typer.Exit: If the size threshold is negative.
    """
    if size_threshold < 0:
        typer.secho("Incorrect size threshold - should not be negative",
                    fg=typer.colors.RED)
        raise typer.Exit()


def count_files(dir_path: str) -> int:
    """
    Count the total number of files in the given directory and its subdirectories.

    Args:
        dir_path (str): The path to the directory to count files in.

    Returns:
        int: The total number of files found.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description=f"Counting files in `{dir_path}` for estimation...", total=None)
        return sum(len(files) for _, _, files in os.walk(dir_path))


def analyze_files_mimetype(
        target_path: str,
        result_storages: list[FiletypeInfoStorage],
        others_storage: FiletypeInfoStorage,
        totals_storage: FiletypeInfoStorage,
        thorough: bool,
) -> tuple[list[FiletypeInfoStorage], FiletypeInfoStorage, FiletypeInfoStorage]:
    """
    Analyze the mimetype of a file and update the corresponding storage.

    Args:
        target_path (str): The path to the file to analyze.
        result_storages (list[FiletypeInfoStorage]): List of storages for different file types.
        others_storage (FiletypeInfoStorage): Storage for files that don't match known types.
        totals_storage (FiletypeInfoStorage): Storage for overall totals.
        thorough (bool): Whether to use thorough analysis (magic library) or not.

    Returns:
        tuple: Updated result_storages, others_storage, and totals_storage.
    """
    if thorough:
        mime_type = magic.from_file(target_path, mime=True)
    else:
        mime_type, _ = mimetypes.guess_type(target_path, strict=False)
        if mime_type is None:
            mime_type = ""
    file_size = os.path.getsize(target_path)
    totals_storage.found_files += 1
    totals_storage.found_size += file_size
    for storage in result_storages:
        if mime_type.startswith(storage.tag):
            storage.found_files += 1
            storage.found_size += file_size
            return result_storages, others_storage, totals_storage
    others_storage.found_files += 1
    others_storage.found_size += file_size
    return result_storages, others_storage, totals_storage


def analyze_file_permissions(file_path: str) -> str | None:
    """
    Analyze the permissions of a file and return a warning message if necessary.

    Args:
        file_path (str): The path to the file to analyze.

    Returns:
        str | None: A warning message if the file has concerning permissions, None otherwise.
    """
    mode = os.stat(file_path).st_mode
    warning_message = None
    if mode & stat.S_IWOTH:
        warning_message = f"WARNING: world-writable - '{file_path}'"

    if mode & stat.S_ISUID:
        warning_message = f"WARNING: SUID is set - '{file_path}'"

    if mode & stat.S_ISGID:
        warning_message = f"WARNING: SGID bit set - '{file_path}'"

    return warning_message


def analyze_dir_permissions(dir_path: str) -> str | None:
    """
    Analyze the permissions of a directory and return a warning message if necessary.

    Args:
        dir_path (str): The path to the directory to analyze.

    Returns:
        str | None: A warning message if the directory is world-writable, None otherwise.
    """
    warning_message = None
    if os.stat(dir_path).st_mode & stat.S_IWOTH:
        warning_message = f"WARNING: world-writable - '{dir_path}'"
    return warning_message


def analyze_filesize(
        file_path: str,
        bigfiles_storage: FiletypeInfoStorage,
        size_threshold: float
    ) -> FiletypeInfoStorage:
    """
    Analyze the size of a file and update the bigfiles_storage if it exceeds the threshold.

    Args:
        file_path (str): The path to the file to analyze.
        bigfiles_storage (FiletypeInfoStorage): Storage for big files information.
        size_threshold (float): The size threshold in GB.

    Returns:
        FiletypeInfoStorage: Updated bigfiles_storage.
    """
    file_size = os.path.getsize(file_path)
    if file_size > size_threshold * (2**30):
        bigfiles_storage.found_files += 1
        bigfiles_storage.found_size += file_size
        bigfiles_storage.found_files_paths.append(file_path)
    return bigfiles_storage


def analyze_directories(root: str, dirs: list[str], permission_warnings: list[str]) -> int:
    """
    Analyze permissions of directories and collect warnings.
    
    Args:
        root (str): The root directory path.
        dirs (list[str]): List of directory names to analyze.
        permission_warnings (list[str]): List to collect permission warnings.
    
    Returns:
        int: Number of errors encountered during analysis.
    """
    errors = 0
    for dir in dirs:
        try:
            permission_warning = analyze_dir_permissions(
                os.path.join(root, dir))
            if permission_warning:
                permission_warnings.append(permission_warning)
        except OSError:
            errors += 1
    return errors


def analyze_files(
    root: str, files: list[str], progress: Progress, task_id: TaskID,
    result_storages: list[FiletypeInfoStorage], others_storage: FiletypeInfoStorage,
    totals_storage: FiletypeInfoStorage, bigfiles_storage: FiletypeInfoStorage,
    permission_warnings: list[str], thorough: bool, size_threshold: float
) -> int:
    """
    Analyze files in a directory, updating various storages and collecting warnings.
    
    Args:
        root (str): The root directory path.
        files (list[str]): List of file names to analyze.
        progress (Progress): Progress bar object.
        task_id (TaskID): ID of the current task in the progress bar.
        result_storages (list[FiletypeInfoStorage]): List of storages for different file types.
        others_storage (FiletypeInfoStorage): Storage for files that don't match known types.
        totals_storage (FiletypeInfoStorage): Storage for overall totals.
        bigfiles_storage (FiletypeInfoStorage): Storage for big files information.
        permission_warnings (list[str]): List to collect permission warnings.
        thorough (bool): Whether to use thorough analysis or not.
        size_threshold (float): The size threshold in GB for big files.
    
    Returns:
        int: Number of errors encountered during analysis.
    """
    errors = 0
    for file in files:
        analysis_target_path = os.path.join(root, file)
        progress.update(task_id, description=analysis_target_path, advance=1)
        try:
            permission_warning = analyze_file_permissions(analysis_target_path)
            if permission_warning:
                permission_warnings.append(permission_warning)

            result_storages, others_storage, totals_storage = analyze_files_mimetype(
                analysis_target_path, result_storages, others_storage, totals_storage, thorough,
            )
            bigfiles_storage = analyze_filesize(
                analysis_target_path, bigfiles_storage, size_threshold)
        except (OSError, magic.MagicException):
            errors += 1
    return errors


def analyze_filesystem(
        root_dir_path: str,
        file_count: int,
        thorough: bool,
        size_threshold: float,
) -> tuple[list[FiletypeInfoStorage], FiletypeInfoStorage, FiletypeInfoStorage, FiletypeInfoStorage, list[str], int]:
    """
    Analyze the entire filesystem starting from the given root directory.
    
    Args:
        root_dir_path (str): The path to the root directory to analyze.
        file_count (int): The total number of files (for progress estimation).
        thorough (bool): Whether to use thorough analysis or not.
        size_threshold (float): The size threshold in GB for big files.
    
    Returns:
        tuple: Contains result_storages, others_storage, totals_storage, bigfiles_storage, 
               permission_warnings, and the count of errors encountered.
    """
    config = get_config()
    result_storages = [
        FiletypeInfoStorage(tag=value['tag'], displayable_name=name) for name, value in config["searchable_types"].items()
    ]
    others_storage = FiletypeInfoStorage(tag="None", displayable_name="Other")
    totals_storage = FiletypeInfoStorage("None", "Total")
    bigfiles_storage = FiletypeInfoStorage("None", "Big")
    permission_warnings: list[str] = list()
    errors_count = 0
    with Progress(
        SpinnerColumn(),
        TimeRemainingColumn(),
        BarColumn(),
        TextColumn(
            "[progress.description]{task.description}", table_column=Column()),
        refresh_per_second=60,
        speed_estimate_period=1,
        transient=True,
    ) as progress:
        analysis_task_id = progress.add_task(
            description=root_dir_path, total=file_count, completed=0
        )
        for root, dirs, files in os.walk(root_dir_path):
            errors_count += analyze_directories(
                root, dirs, permission_warnings
            )
            errors_count += analyze_files(
                root, files, progress, analysis_task_id,
                result_storages, others_storage, totals_storage,
                bigfiles_storage, permission_warnings,
                thorough, size_threshold
            )

    return (
        result_storages,
        others_storage,
        totals_storage,
        bigfiles_storage,
        permission_warnings,
        errors_count,
    )


def build_rich_table(
        result_storages: list[FiletypeInfoStorage],
        others_storage: FiletypeInfoStorage,
        totals_storage: FiletypeInfoStorage,
        bigfiles_storage: FiletypeInfoStorage,
        errored_files_count: int,
        size_threshold: float,
) -> Table:
    """
    Display the results of the filesystem analysis in a formatted table.
    
    Args:
        result_storages (list[FiletypeInfoStorage]): List of storages for different file types.
        others_storage (FiletypeInfoStorage): Storage for files that don't match known types.
        totals_storage (FiletypeInfoStorage): Storage for overall totals.
        bigfiles_storage (FiletypeInfoStorage): Storage for big files information.
        errored_files_count (int): Number of files that couldn't be analyzed due to errors.
        analysis_duration (timedelta): The total duration of the analysis.
        size_threshold (float): The size threshold in GB used for big files.
    """
    result_table = Table(title="Directory analysis results")
    result_table.add_column("Media type")
    result_table.add_column("Files found")
    result_table.add_column("Size")
    for storage in result_storages:
        result_table.add_row(
            storage.displayable_name,
            str(storage.found_files),
            str(naturalsize(storage.found_size)),
        )
    result_table.add_row(
        others_storage.displayable_name,
        str(others_storage.found_files),
        str(naturalsize(others_storage.found_size)),
    )
    result_table.add_section()
    result_table.add_row(
        "Big Files",
        str(bigfiles_storage.found_files),
        str(naturalsize(bigfiles_storage.found_size))
    )
    result_table.add_row(f"[italic]Files bigger than {size_threshold} GB")
    result_table.add_section()
    result_table.add_row(
        "Errors",
        str(errored_files_count),
        "n/a",
    )
    result_table.add_section()
    result_table.add_row(
        "Totals",
        str(totals_storage.found_files),
        str(naturalsize(totals_storage.found_size)),
    )
    return result_table


def main(
    dir_path: Annotated[str, typer.Argument(help="Path to directory that needs to be analyzed")],
    thorough: bool = False,
    size_threshold: Annotated[float, typer.Option(
        help="File size in GiB that gets the file marked")] = 1,
    output_path: Annotated[str, typer.Option(
        help="Path where reults will be output")] = "",
) -> None:
    check_path(dir_path)
    check_size_threshold(size_threshold)

    file_count = count_files(dir_path)
    print(f"Preliminary file count: {file_count}")

    analysis_start_dt = datetime.now()
    (
        result_storages,
        others_storage,
        totals_storage,
        big_files_storage,
        permission_warnings,
        errored_files_count
    ) = analyze_filesystem(
        dir_path,
        file_count,
        thorough,
        size_threshold
    )
    analysis_duration = datetime.now() - analysis_start_dt

    rich_table = build_rich_table(
        result_storages, others_storage,
        totals_storage, big_files_storage, errored_files_count, size_threshold)
    
    if output_path == "":
        rich_print(rich_table)
        rich_print(f"Analysis duration: {analysis_duration}")
    else:
        with open(output_path, 'w') as file:
            console = Console(file=file)
            console.print(rich_table)
            console.print(f"Analysis duration: {analysis_duration}")
        print(f"Analysis results written in '{output_path}'")

    with open(BIGFILES_OUTPUT_PATH, 'w') as f:
        f.write("\n".join(big_files_storage.found_files_paths))
    with open(PERMISSIONS_OUTPUT_PATH, 'w') as f:
        f.write("\n".join(permission_warnings))


if __name__ == "__main__":
    typer.run(main)
