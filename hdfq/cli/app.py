import sys
from pathlib import Path
from typing import Annotated, Optional, cast

import ch5mpy as ch
import click
import tomllib
import typer
from typer.rich_utils import rich_format_error

from hdfq.hdfq import run
from hdfq.repair import repair_group

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, no_args_is_help=True)


def version_callback(value: bool):
    if value:
        with open("pyproject.toml", mode="rb") as project_file:
            project = tomllib.load(project_file)
            version = project["tool"]["poetry"]["version"]
        print(f"hdfq-{version}")
        raise typer.Exit()


@app.callback(invoke_without_command=True, no_args_is_help=True)
# @app.command(no_args_is_help=True)
def main(
    ctx: typer.Context,
    filter: Annotated[str, typer.Argument(help="Command filter to evaluate", show_default=False)],
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a hdf5 file to run the filter on",
            show_default=False,
        ),
    ] = cast(Path, ... if sys.stdin.isatty() else Path(sys.stdin.read().strip())),
    version: Annotated[
        Optional[bool], typer.Option("--version", help="Print current version and quit", callback=version_callback)
    ] = None,
) -> None:
    """
    Command-line processor for viewing and manipulating objects and attributes in a HDF5 file.
    It uses a syntax similar to jq's.
    See https://gitlab.vidium.fr/vidium/hdfq for documentation on supported filters.
    """
    if filter == "repair":
        return repair(ctx, path)

    if not path.exists():
        rich_format_error(click.UsageError(f"{path} does not exist for 'PATH'.", ctx=ctx))

        raise typer.Exit(code=1)

    run(filter, path)


@app.command(no_args_is_help=True)
def repair(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a hdf5 file to repair",
            show_default=False,
        ),
    ] = cast(Path, ... if sys.stdin.isatty() else Path(sys.stdin.read().strip())),
    verbose: bool = False,
) -> None:
    """
    Repair corrupted HDF5 file by extracting valid groups and datasets.
    """
    if not path.exists():
        rich_format_error(click.UsageError(f"{path} does not exist for 'PATH'.", ctx=ctx))

        raise typer.Exit(code=1)

    restore_path = path.with_stem("~" + path.stem)

    with ch.File(path, mode=ch.H5Mode.READ) as corrupted_file, ch.File(
        restore_path, mode=ch.H5Mode.WRITE_TRUNCATE
    ) as new_file:
        repair_group(corrupted_file, new_file, verbose)

    path.unlink()
    restore_path.rename(path)


if __name__ == "__main__":
    commands = {"main", "repair"}
    if sys.argv[1] not in commands:
        sys.argv.insert(1, "main")
    app()
