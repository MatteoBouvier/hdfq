from typing import Any, Literal, Protocol

import ch5mpy as ch

from hdfq.display import display
from hdfq.exceptions import EvalError
from hdfq.parser import Node, Special, Tree, VTNode

EVAL_OBJECT = ch.H5Dict[Any] | ch.Dataset[Any] | ch.AttributeManager | list[str] | dict[str, Any]


class EVAL_FUNC_base(Protocol):
    def __call__(self, obj: EVAL_OBJECT) -> EVAL_OBJECT: ...


class EVAL_FUNC_get(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT: ...


class EVAL_FUNC_set(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str, value: Any) -> EVAL_OBJECT: ...


EVAL_FUNC = EVAL_FUNC_base | EVAL_FUNC_get | EVAL_FUNC_set


def get_object(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict)):
        raise EvalError(f"Cannot get object from '{type(obj).__name__}'")

    return obj[key]


def get_attribute(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attribute from '{type(obj).__name__}'")

    return obj.attributes[key]


def get_keys(obj: EVAL_OBJECT) -> list[str]:
    if not isinstance(obj, ch.H5Dict):
        raise EvalError(f"Cannot get keys from '{type(obj).__name__}'")

    return list(obj.keys())


def get_attributes(obj: EVAL_OBJECT) -> dict[str, Any]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attributes from '{type(obj).__name__}'")

    return obj.attributes.as_dict()


def get_attribute_keys(obj: EVAL_OBJECT) -> list[str]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attribute keys from '{type(obj).__name__}")

    return list(obj.attributes.keys())


def set_key_value(obj: EVAL_OBJECT, key: str, value: Any) -> None:
    if not isinstance(obj, (ch.H5Dict, dict, ch.AttributeManager)):
        raise EvalError(f"Cannot assign value to '{type(obj).__name__}'")

    obj[key] = value


def del_object(obj: EVAL_OBJECT, key: str) -> None:
    if not isinstance(obj, (ch.H5Dict, dict, ch.AttributeManager)):
        raise EvalError(f"Cannot delete value from '{type(obj).__name__}'")

    del obj[key]


def shallow_eval_statement(target: VTNode, context: EVAL_OBJECT) -> tuple[EVAL_OBJECT, str]:
    context, key = eval_statement(target.target, context), target.value
    assert isinstance(key, str)

    if target.name == "GetAttr":
        if not isinstance(context, ch.H5Dict):
            raise EvalError(f"Cannot get attribute '{key}' from {type(context).__name__}")
        context = context.attributes

    return context, key


def eval_statement(statement: Node | Literal[Special.context], context: EVAL_OBJECT) -> EVAL_OBJECT:
    match statement:
        case Node(name="Display"):
            display(context)

        case Node(name="Keys"):
            context = get_keys(context)

        case Node(name="Attrs"):
            context = get_attributes(context)

        case Node(name="AttrKeys"):
            context = get_attribute_keys(context)

        case Node(name="Get", target=target, value=value):
            context = get_object(eval_statement(target, context), value)

        case Node(name="GetAttr", target=target, value=value):
            context = get_attribute(eval_statement(target, context), value)

        case Node(name="Assign", target=target, value=value):
            value = eval_statement(value, context)
            context, key = shallow_eval_statement(target, context)
            set_key_value(context, key, value)

        case Node(name="Del", target=target, value=value):
            context = eval_statement(target, context)
            context, value = shallow_eval_statement(value, context)
            assert isinstance(value, str), "not str : " + str(type(value))
            del_object(context, value)

        case Node(name="Constant", value=value):
            context = value

    return context


def eval(tree: Tree, context: EVAL_OBJECT) -> None:
    for statement in tree.body:
        context = eval_statement(statement, context)
