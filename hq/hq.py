import ch5mpy as ch
import typer

from hq.evaluation import eval
from hq.parser import parse

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(pattern: str, path: str) -> None:
    tree = parse(pattern)

    with ch.options(error_mode="ignore"):
        h5_object = ch.H5Dict.read(path, mode=ch.H5Mode.READ_WRITE_CREATE)
        eval(tree, h5_object)


if __name__ == "__main__":
    app()
