from __future__ import annotations

import re
from enum import Enum
from typing import Any, Iterable, NamedTuple, Protocol, cast

import ch5mpy as ch

from hq.exceptions import ParseError

PARSE_OBJECT = ch.H5Dict[Any] | ch.Dataset[Any] | list[str] | dict[str, Any]


class PARSE_FUNC_base(Protocol):
    def __call__(self, obj: PARSE_OBJECT) -> PARSE_OBJECT:
        ...


class PARSE_FUNC_get(Protocol):
    def __call__(self, obj: PARSE_OBJECT, key: str) -> PARSE_OBJECT:
        ...


class PARSE_FUNC_set(Protocol):
    def __call__(self, obj: PARSE_OBJECT, key: str, value: Any) -> PARSE_OBJECT:
        ...


PARSE_FUNC = PARSE_FUNC_base | PARSE_FUNC_get | PARSE_FUNC_set


def repr_dict(key_value: tuple[str, Any]) -> str:
    k, v = key_value
    return f"{repr(k)}: {repr(v)}"


def display(obj: PARSE_OBJECT) -> PARSE_OBJECT:
    if isinstance(obj, ch.H5Dict):
        print(repr(obj)[6:])

    elif isinstance(obj, list):
        print("[\n\t" + ",\n\t".join(map(repr, obj)) + "\n]")

    elif isinstance(obj, dict):
        print("{\n\t" + ",\n\t".join(map(repr_dict, obj.items())) + "\n}")

    else:
        print(repr(obj))

    return obj


def get_object(obj: PARSE_OBJECT, key: str) -> PARSE_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict)):
        raise ParseError

    return obj[key]


def get_attribute(obj: PARSE_OBJECT, key: str) -> PARSE_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return obj.attributes[key]


def get_keys(obj: PARSE_OBJECT) -> list[str]:
    if not isinstance(obj, ch.H5Dict):
        raise ParseError

    return list(obj.keys())


def get_attributes(obj: PARSE_OBJECT) -> dict[str, Any]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return obj.attributes.as_dict()


def get_keys_attributes(obj: PARSE_OBJECT) -> list[str]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return list(obj.attributes.keys())


def set_key_value(obj: PARSE_OBJECT, key: str, value: Any) -> PARSE_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict)):
        raise ParseError

    obj[key] = value

    return obj


def set_attribute_key_value(obj: PARSE_OBJECT, key: str, value: Any) -> PARSE_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    obj.attributes[key] = value

    return obj.attributes.as_dict()


class Node(NamedTuple):
    name: str
    function: PARSE_FUNC
    args: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return f"{self.name}({','.join(self.args)})"

    def with_args(self, *args: str) -> Node:
        return Node(self.name, self.function, args)

    def run(self, obj: PARSE_OBJECT) -> PARSE_OBJECT:
        if self.args is None:
            return cast(PARSE_FUNC_base, self.function)(obj)
        return self.function(obj, *self.args)


class Nodes(Node, Enum):  # pyright: ignore[reportIncompatibleVariableOverride]
    Display = Node("Display", function=display)
    Keys = Node("Keys", get_keys)
    Get = Node("Get", get_object)
    Set = Node("Set", set_key_value)
    Attrs = Node("Attrs", get_attributes)
    Attr_keys = Node("Attr_keys", get_keys_attributes)
    Attr_get = Node("Attr_get", get_attribute)
    Attr_set = Node("Attr_set", set_attribute_key_value)


class Tokens(str, Enum):
    GET = "."
    GET_ATTR = "#"
    SET = "="
    KEYS = "keys"
    ATTRS = "attrs"
    ATTR_KEYS = "kattrs"
    DEL = "del"


def _get_next_4(tokens_list: list[str], index: int) -> tuple[str, str | None, str | None, str | None]:
    return (
        tokens_list[index],
        tokens_list[index + 1] if index + 1 < len(tokens_list) else None,
        tokens_list[index + 2] if index + 2 < len(tokens_list) else None,
        tokens_list[index + 3] if index + 3 < len(tokens_list) else None,
    )


def tokens(group: str) -> Iterable[str | tuple[str, str] | tuple[str, str, str, str]]:
    if group in {"", "."}:
        return

    tokens_list = list(filter(None, re.split(r"([^a-zA-Z0-9_'\"-])", group)))

    i = 0
    while i < len(tokens_list):
        a, b, c, d = _get_next_4(tokens_list, i)

        if a in {Tokens.GET, Tokens.GET_ATTR}:
            if c == Tokens.SET:
                if b is None or c is None or d is None:
                    raise ParseError

                yield a, b, c, d
                i += 4

            else:
                if b is None:
                    raise ParseError

                yield a, b
                i += 2

        elif a == "del":
            pass

        else:
            yield a
            i += 1


class Tree:
    def __init__(self) -> None:
        self.body: list[Node] = []

    def __repr__(self) -> str:
        return f"AST(\n\tbody={self.body}\n)"

    def run(self, h5_object: PARSE_OBJECT) -> None:
        for node in self.body:
            h5_object = node.run(h5_object)


def parse(pattern: str) -> Tree:
    tree = Tree()

    for group in pattern.replace(" ", "").split("|"):
        for operation in tokens(group):
            match operation:
                case Tokens.KEYS:
                    tree.body.append(Nodes.Keys)

                case Tokens.ATTRS:
                    tree.body.append(Nodes.Attrs)

                case Tokens.ATTR_KEYS:
                    tree.body.append(Nodes.Attr_keys)

                case Tokens.GET, key:
                    tree.body.append(Nodes.Get.with_args(key))

                case Tokens.GET, key, Tokens.SET, value:
                    tree.body.append(Nodes.Set.with_args(key, value))

                case Tokens.GET_ATTR, attr:
                    tree.body.append(Nodes.Attr_get.with_args(attr))

                case Tokens.GET_ATTR, key, Tokens.SET, value:
                    tree.body.append(Nodes.Attr_set.with_args(key, value))

                case _:
                    raise ParseError

    tree.body.append(Nodes.Display)

    return tree
