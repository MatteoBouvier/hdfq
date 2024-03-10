from __future__ import annotations

import io
import re
from typing import TYPE_CHECKING, Any

import ch5mpy as ch
import numpy as np
import rich.box
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.table import Table
from rich.theme import Theme

if TYPE_CHECKING:
    from hq.evaluation import EVAL_OBJECT


class H5Highlighter(RegexHighlighter):
    base_style = "h5."
    highlights = [
        r"(?P<bool_true>True)",
        r"(?P<bool_false>False)",
        r"(?P<str>[\"'][a-zA-Z_]\w*[\"'])",
        r"(?P<number>(?<!\w)[+-]?\d+(?:\.\d*)?(?!\w))",
        r"(?P<identifier>\.\w+(?=:))",
        r"(?P<attribute>#\w+(?=:))",
        r"(?P<value>\w+(?==))",
        r"(?P<builtin>(?<!\w)(None|int\d*|float\d*|<U\d+))",
    ]


theme = Theme(
    {
        "h5.bool_true": "bold green",
        "h5.bool_false": "bold red",
        "h5.str": "green",
        "h5.number": "cyan",
        "h5.identifier": "bold yellow",
        "h5.attribute": "italic grey70",
        "h5.value": "blue",
        "h5.builtin": "orchid",
    }
)
console = Console(highlighter=H5Highlighter(), theme=theme)


def get_tabs(offset: int) -> str:
    return "  " * offset


def repr_dict(obj: dict[str, Any] | ch.AttributeManager | ch.H5Dict, offset: int) -> str:
    prefix = "." if isinstance(obj, (dict, ch.H5Dict)) else "#"
    tabs = get_tabs(offset)
    return (
        f"{tabs}"
        + f",\n{tabs}".join(map(lambda kv: f"{prefix}{kv[0]}: {repr_object(kv[1], offset=offset)}", obj.items()))
        + ",\n"
    )


def repr_object(obj: EVAL_OBJECT, offset: int) -> str:
    if isinstance(obj, ch.H5Dict):
        if len(obj.keys()) + len(obj.attributes) == 0:
            return "{}"

        if len(obj.attributes):
            attributes = repr_dict(obj.attributes, offset=offset + 1)
        else:
            attributes = ""

        if len(obj):
            body = repr_dict(obj, offset=offset + 1)
        else:
            body = ""

        tabs = get_tabs(offset)

        return f"{{\n{attributes}{body}{tabs}}}"

    elif isinstance(obj, (dict, ch.AttributeManager)):
        if offset > 0:
            return repr_dict(obj, offset=offset)

        return f"{{\n{repr_dict(obj, offset=offset+1)}}}"

    elif isinstance(obj, list):
        tabs = get_tabs(offset + 1)
        content_repr = f",\n{tabs}".join(map(repr, obj))
        return f"[\n{tabs}{content_repr}\n]"

    elif isinstance(obj, ch.H5Array):
        if obj.size == 0:
            return "[]"

        if obj.ndim == 0:
            return str(obj)

        table = Table(show_header=False, show_lines=False, box=rich.box.ROUNDED)
        if obj.ndim == 1:
            table.add_row(*map(repr, obj[:3]), "...", *map(repr, obj[-3:]))  # pyright: ignore[reportArgumentType]

        elif obj.ndim == 2:
            for row in range(obj.shape[1]):
                table.add_row(*map(str, obj[row]))  # pyright: ignore[reportArgumentType]

        else:
            table.add_row("...")

        tabs = get_tabs(offset)

        table_console = Console(file=io.StringIO(), width=console.width - 1 - len(tabs))
        table_console.print(f".shape={obj.shape}  .dtype={obj.dtype}", table)
        table_repr = table_console.file.getvalue().rstrip()  # pyright: ignore[reportAttributeAccessIssue]
        table_repr = re.sub("\n", f"\n{tabs}", table_repr)

        return table_repr

    elif isinstance(obj, np.void):
        return re.sub(
            r"\.$", "", re.sub(r"\.+", ".", "".join(chr(c) if 32 <= c < 128 else "." for c in bytes(obj)[13:]))
        )

    else:
        return repr(obj)


def display(obj: EVAL_OBJECT) -> None:
    console.print(repr_object(obj, offset=0))
