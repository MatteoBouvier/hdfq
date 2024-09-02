from tempfile import NamedTemporaryFile

import ch5mpy as ch
import numpy as np

from hdfq import eval
from hdfq.parser import parse


def test_evaluate_dataset_creation_empty():
    tree, _ = parse(".a = []")

    tmp_file = NamedTemporaryFile()
    with ch.File(tmp_file.name, mode="r+") as file:
        h5_object = ch.H5Dict(file)

        eval(tree, h5_object)

        assert isinstance(h5_object["a"], ch.H5Array)
        assert h5_object["a"].shape == (0,)
        assert h5_object["a"].dtype == np.float32


def test_evaluate_dataset_creation():
    tree, _ = parse(".a = [0.0](20, 20)")

    tmp_file = NamedTemporaryFile()
    with ch.File(tmp_file.name, mode="r+") as file:
        h5_object = ch.H5Dict(file)

        eval(tree, h5_object)

        assert isinstance(h5_object["a"], ch.H5Array)
        assert h5_object["a"].shape == (20, 20)
        assert np.all(h5_object["a"] == 0)
        assert h5_object["a"].dtype == np.float32


def test_evaluate_dataset_creation_array():
    tree, _ = parse(".a = [0, 1, 2]")

    tmp_file = NamedTemporaryFile()
    with ch.File(tmp_file.name, mode="r+") as file:
        h5_object = ch.H5Dict(file)

        eval(tree, h5_object)

        assert isinstance(h5_object["a"], ch.H5Array)
        assert h5_object["a"].shape == (20, 20)
        assert np.array_equal(h5_object["a"], [0, 1, 2])
        assert h5_object["a"].dtype == np.int32
