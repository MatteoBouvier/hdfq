from pathlib import Path

import ch5mpy as ch

from hdfq.evaluation import eval as hdfq_eval
from hdfq.parser import parse


def run(filter: str, path: Path) -> None:
    tree, requires_write_access = parse(filter)
    mode = ch.H5Mode.READ_WRITE if requires_write_access else ch.H5Mode.READ

    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path, mode=mode)
        hdfq_eval(tree, h5_object)
