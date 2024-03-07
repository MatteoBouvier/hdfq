import typer

import ch5mpy as ch
from hq.parse import parse


def main(path: str, pattern: str) -> None:
    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path)

        for token in parse(pattern):
            h5_object = token(h5_object)


if __name__ == "__main__":
    typer.run(main)
