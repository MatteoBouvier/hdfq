import sys
from pathlib import Path
from typing import Annotated, cast

import ch5mpy as ch
import click
import typer
from typer.rich_utils import rich_format_error

from hdfq.repair import repair_group

tools = typer.Typer(add_completion=False, pretty_exceptions_enable=False, no_args_is_help=True)


@tools.command(no_args_is_help=True)
def repair(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a hdf5 file to repair",
            show_default=False,
        ),
    ] = cast(Path, ... if sys.stdin.isatty() else Path(sys.stdin.read().strip())),
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="verbose output")] = False,
    in_RAM_copy: Annotated[bool, typer.Option("--in-RAM-copy", "-R", help="perform in-RAM copy of datasets")] = False,
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
        repair_group(corrupted_file, new_file, verbose, in_RAM_copy)

    path.unlink()
    restore_path.rename(path)


if __name__ == "__main__":
    tools()
