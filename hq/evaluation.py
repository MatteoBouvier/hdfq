from typing import Any, Protocol

import ch5mpy as ch

from hq.exceptions import ParseError
from hq.parser import Special, Tree

EVAL_OBJECT = ch.H5Dict[Any] | ch.Dataset[Any] | list[str] | dict[str, Any]


class EVAL_FUNC_base(Protocol):
    def __call__(self, obj: EVAL_OBJECT) -> EVAL_OBJECT: ...


class EVAL_FUNC_get(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT: ...


class EVAL_FUNC_set(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str, value: Any) -> EVAL_OBJECT: ...


EVAL_FUNC = EVAL_FUNC_base | EVAL_FUNC_get | EVAL_FUNC_set


def repr_dict(key_value: tuple[str, Any]) -> str:
    k, v = key_value
    return f"{repr(k)}: {repr(v)}"


def display(obj: EVAL_OBJECT) -> EVAL_OBJECT:
    if isinstance(obj, ch.H5Dict):
        print(repr(obj)[6:])

    elif isinstance(obj, list):
        print("[\n\t" + ",\n\t".join(map(repr, obj)) + "\n]")

    elif isinstance(obj, dict):
        print("{\n\t" + ",\n\t".join(map(repr_dict, obj.items())) + "\n}")

    else:
        print(repr(obj))

    return obj


def get_object(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict)):
        raise ParseError

    return obj[key]


def get_attribute(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return obj.attributes[key]


def get_keys(obj: EVAL_OBJECT) -> list[str]:
    if not isinstance(obj, ch.H5Dict):
        raise ParseError

    return list(obj.keys())


def get_attributes(obj: EVAL_OBJECT) -> dict[str, Any]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return obj.attributes.as_dict()


def get_keys_attributes(obj: EVAL_OBJECT) -> list[str]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    return list(obj.attributes.keys())


def set_key_value(obj: EVAL_OBJECT, key: str, value: Any) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict)):
        raise ParseError

    obj[key] = value

    return obj


def set_attribute_key_value(obj: EVAL_OBJECT, key: str, value: Any) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise ParseError

    obj.attributes[key] = value

    return obj.attributes.as_dict()


def del_object(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    return obj


def eval(tree: Tree, context: ch.H5Dict) -> None:
    pass
