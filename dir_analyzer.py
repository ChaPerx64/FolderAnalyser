from typing import Annotated
import os
import typer
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table, Column
import magic
from dataclasses import dataclass
from humanize import naturalsize

searchable_types = {
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


@dataclass
class FiletypeInfoStorage:
    tag: str
    found_files = 0
    found_size = 0
    displayable_name: str


def analyze_file(
    target_path: str,
    result_storages: list[FiletypeInfoStorage],
    others_storage: FiletypeInfoStorage,
    totals_storage: FiletypeInfoStorage,
    errored_files_count: int,
) -> tuple[list[FiletypeInfoStorage], FiletypeInfoStorage, FiletypeInfoStorage, int]:
    counted = False
    try:
        mime_type = magic.from_file(target_path, mime=True)
        file_size = os.path.getsize(target_path)
        totals_storage.found_files += 1
        totals_storage.found_size += file_size
        for storage in result_storages:
            if mime_type.startswith(storage.tag):
                storage.found_files += 1
                storage.found_size += file_size
                counted = True
        if not counted:
            others_storage.found_files += 1
            others_storage.found_size += file_size
    except OSError:
        errored_files_count += 1
    return (
        result_storages,
        others_storage,
        totals_storage,
        errored_files_count
    )


def count_files(dir_path: str) -> int:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description=f"Counting files in `{dir_path}` for estimation...", total=None)
        file_count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_count += 1
    return file_count


def analyze_directory(dir_path: str, file_count: int) -> tuple[list[FiletypeInfoStorage], FiletypeInfoStorage, FiletypeInfoStorage, int]:
    result_storages = [
        FiletypeInfoStorage(tag=value['tag'], displayable_name=name) for name, value in searchable_types.items()
    ]
    others_storage = FiletypeInfoStorage(tag="None", displayable_name="Other")
    totals_storage = FiletypeInfoStorage("None", "Total")
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
        analysis_target_path = str(dir_path)
        analysis_task_id = progress.add_task(
            description=analysis_target_path, total=file_count, completed=analyzed_files
        )
        errored_files_count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                analyzed_files += 1
                analysis_target_path = os.path.join(root, file)
                (
                    result_storages,
                    others_storage,
                    totals_storage,
                    errored_files_count
                ) = analyze_file(
                    analysis_target_path,
                    result_storages,
                    others_storage,
                    totals_storage,
                    errored_files_count
                )
                progress.update(
                    analysis_task_id, description=analysis_target_path, completed=analyzed_files)
    return (
        result_storages,
        others_storage,
        totals_storage,
        errored_files_count
    )


def main(
    dir_path: Annotated[str, typer.Argument(help="Path to directory that needs to be analyzed")],
    size_treshold: Annotated[float, typer.Option(
        help="File size in GiB that gets the file marked")] = 1,
    output_path: Annotated[str, typer.Option(
        help="Path where reults will be output")] = "",
) -> None:

    if not os.path.exists(dir_path):
        typer.secho("Incorrect path - does not exist", fg=typer.colors.RED)
        raise typer.Exit()
    if not os.path.isdir(dir_path):
        typer.secho("Incorrect path - should be a directory",
                    fg=typer.colors.RED)
        raise typer.Exit()

    file_count = count_files(dir_path)
    print(f"Preliminary file count: {file_count}")

    result_storages, others_storage, totals_storage, errored_files_count = analyze_directory(
        dir_path, file_count)

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


if __name__ == "__main__":
    typer.run(main)
