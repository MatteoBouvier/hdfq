import sys

import ch5mpy as ch
import typer

from hq.evaluation import eval
from hq.parser import parse


def main(path: str, pattern: str) -> None:
    sys.tracebacklimit = 0

    tree = parse(pattern)

    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path, mode=ch.H5Mode.READ_WRITE_CREATE)
        eval(tree, h5_object)


if __name__ == "__main__":
    typer.run(main)
