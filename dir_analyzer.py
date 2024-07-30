import mimetypes
import os
import stat
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Annotated, Any
import json

import magic
import typer
from humanize import naturalsize
from rich import print
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeRemainingColumn)
from rich.table import Column, Table


CONFIG_PATH = "./config.json"

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
    if not os.path.exists(path):
        typer.secho("Incorrect path - does not exist", fg=typer.colors.RED)
        raise typer.Exit()
    if not os.path.isdir(path):
        typer.secho("Incorrect path - should be a directory",
                    fg=typer.colors.RED)
        raise typer.Exit()


def check_size_threshold(size_threshold: float) -> None:
    if size_threshold < 0:
        typer.secho("Incorrect size threshold - should not be negative",
                    fg=typer.colors.RED)
        raise typer.Exit()


def count_files(dir_path: str) -> int:
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
    warning_message = None
    if os.stat(dir_path).st_mode & stat.S_IWOTH:
        warning_message = f"WARNING: world-writable - '{dir_path}'"
    return warning_message


def analyze_filesize(file_path: str, bigfiles_storage: FiletypeInfoStorage, size_threshold: float) -> FiletypeInfoStorage:
    file_size = os.path.getsize(file_path)
    if file_size > size_threshold * (2**30):
        bigfiles_storage.found_files += 1
        bigfiles_storage.found_size += file_size
        bigfiles_storage.found_files_paths.append(file_path)
    return bigfiles_storage


def analyze_filesystem(
        root_dir_path: str,
        file_count: int,
        thorough: bool,
        size_threshold: float,
) -> tuple[list[FiletypeInfoStorage], FiletypeInfoStorage, FiletypeInfoStorage, FiletypeInfoStorage, list[str], int]:
    config = get_config()
    result_storages = [
        FiletypeInfoStorage(tag=value['tag'], displayable_name=name) for name, value in config["searchable_types"].items()
    ]
    others_storage = FiletypeInfoStorage(tag="None", displayable_name="Other")
    totals_storage = FiletypeInfoStorage("None", "Total")
    bigfiles_storage = FiletypeInfoStorage("None", "Big")
    permission_warnings: list[str] = list()
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
        analyzed_files = 0
        analysis_task_id = progress.add_task(
            description=root_dir_path, total=file_count, completed=analyzed_files
        )
        errors_count = 0
        for root, dirs, files in os.walk(root_dir_path):
            for dir in dirs:
                try:
                    permission_warning = analyze_dir_permissions(
                        os.path.join(root, dir))
                    if permission_warning:
                        permission_warnings.append(permission_warning)
                except OSError:
                    errors_count += 1
            for file in files:
                analysis_target_path = os.path.join(root, file)
                progress.update(
                    analysis_task_id, description=analysis_target_path, completed=analyzed_files)
                try:
                    permission_warning = analyze_file_permissions(
                        analysis_target_path)
                    if permission_warning:
                        permission_warnings.append(permission_warning)
                    result_storages, others_storage, totals_storage = analyze_files_mimetype(
                        analysis_target_path,
                        result_storages,
                        others_storage,
                        totals_storage,
                        thorough,
                    )
                    bigfiles_storage = analyze_filesize(
                        analysis_target_path, bigfiles_storage, size_threshold)
                except (OSError, magic.MagicException):
                    errors_count += 1
                analyzed_files += 1
    return (
        result_storages,
        others_storage,
        totals_storage,
        bigfiles_storage,
        permission_warnings,
        errors_count,
    )


def display_results(
        result_storages: list[FiletypeInfoStorage],
        others_storage: FiletypeInfoStorage,
        totals_storage: FiletypeInfoStorage,
        bigfiles_storage: FiletypeInfoStorage,
        errored_files_count: int,
        analysis_duration: timedelta,
        size_threshold: float,
) -> None:
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
    print(result_table)
    print(f"Analysis duration: {analysis_duration}")


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

    display_results(
        result_storages, others_storage,
        totals_storage, big_files_storage, errored_files_count, analysis_duration, size_threshold)

    with open('bigfiles.txt', 'w') as f:
        f.write("\n".join(big_files_storage.found_files_paths))
    with open('permissions.txt', 'w') as f:
        f.write("\n".join(permission_warnings))


if __name__ == "__main__":
    typer.run(main)
