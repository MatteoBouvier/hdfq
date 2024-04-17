import sys
from pathlib import Path
from typing import Annotated, Optional, cast

import click
import tomllib
import typer
from typer.rich_utils import rich_format_error

from hdfq.hdfq import run

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, no_args_is_help=True)


def version_callback(value: bool):
    if value:
        with open(Path(__file__).parents[2] / "pyproject.toml", mode="rb") as project_file:
            project = tomllib.load(project_file)
            version = project["tool"]["poetry"]["version"]
        print(f"hdfq-{version}")
        raise typer.Exit()


@app.command(no_args_is_help=True)
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
    if not path.exists():
        rich_format_error(click.UsageError(f"{path} does not exist for 'PATH'.", ctx=ctx))

        raise typer.Exit(code=1)

    run(filter, path)


if __name__ == "__main__":
    app()
