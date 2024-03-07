import functools
import re
from enum import Enum
from typing import Any, Callable, Generator, Iterable, NamedTuple

import ch5mpy as ch
from hq.exceptions import ParseError

PARSE_OBJECT = ch.H5Dict[Any] | ch.Dataset[Any] | list[str] | dict[str, Any]


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
    if isinstance(obj, (list, ch.Dataset)):
        raise ParseError

    return obj[key]


def get_attribute(obj: PARSE_OBJECT, attr: str) -> None:
    if isinstance(obj, list):
        raise ParseError

    return obj.attributes[attr]


def get_keys(obj: PARSE_OBJECT) -> list[str]:
    if isinstance(obj, (list, ch.Dataset)):
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


class Token(NamedTuple):
    type: str
    function: Callable
    arg: str | None = None

    def __call__(self, obj: ch.H5Dict[Any]) -> ch.H5Dict[Any]:
        if self.arg is None:
            return self.function(obj)
        return self.function(obj, self.arg)


class Tokens(functools.partial[Token], Enum):
    Get = functools.partial(Token, "Get", get_object)
    Get_attr = functools.partial(Token, "Get_attr", get_attribute)
    Display = functools.partial(Token, "Display", display)
    Keys = functools.partial(Token, "Keys", get_keys)
    Attributes = functools.partial(Token, "Attributes", get_attributes)
    Keys_attr = functools.partial(Token, "Keys_attr", get_keys_attributes)


def iter_operations(group: str) -> Iterable[str | tuple[str, str]]:
    it = filter(None, re.split(r"(\W)", group))
    for n in it:
        if n in {".", "#"}:
            yield n, next(it)

        else:
            yield n


def parse(pattern: str) -> Generator[Token, None, None]:
    for group in pattern.replace(" ", "").split("|"):
        for operation in iter_operations(group):
            match operation:
                case "keys":
                    yield Tokens.Keys()

                case "attrs":
                    yield Tokens.Attributes()

                case "kattrs":
                    yield Tokens.Keys_attr()

                case ".", key:
                    yield Tokens.Get(key)

                case "#", attr:
                    yield Tokens.Get_attr(attr)

                case _:
                    raise ParseError

    yield Tokens.Display()
