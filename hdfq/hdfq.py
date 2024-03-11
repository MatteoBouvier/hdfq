from typing import Annotated

import ch5mpy as ch
import typer

from hdfq.evaluation import eval as hdfq_eval
from hdfq.parser import parse

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(
    filter: Annotated[str, typer.Argument(help="Command filter to evaluate", show_default=False)],
    path: Annotated[str, typer.Argument(help="Path to a hdf5 file to run the filter on", show_default=False)],
) -> None:
    """
    Command-line processor for viewing and manipulating objects and attributes in a HDF5 file.
    It uses a syntax similar to jq's.
    See https://gitlab.vidium.fr/vidium/hdfq for documentation on supported filters.
    """
    tree = parse(filter)

    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path, mode=ch.H5Mode.READ_WRITE_CREATE)
        hdfq_eval(tree, h5_object)


if __name__ == "__main__":
    app()
