import ch5mpy as ch
import typer

from hq.parse import parse


def main(path: str, pattern: str) -> None:
    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path, mode=ch.H5Mode.READ_WRITE_CREATE)

        tree = parse(pattern)
        tree.run(h5_object)


if __name__ == "__main__":
    typer.run(main)
