from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import ch5mpy as ch
import numpy.typing as npt

from hdfq.display import display, nice_size_format
from hdfq.exceptions import EvalError
from hdfq.parser import Node, Special, Tree, VTNode


@dataclass
class DatasetInfo:
    shape: tuple[int, ...] | None
    dtype: str
    data: ch.Dataset[Any] | npt.NDArray[Any] | None
    chunks: bool
    maxshape: tuple[int | None, ...] | bool


EVAL_OBJECT = (
    ch.H5Dict[Any]
    | ch.Dataset[Any]
    | ch.AttributeManager
    | ch.H5List[ch.H5Dict[Any] | ch.Dataset[Any]]
    | list[str]
    | dict[str, Any]
    | DatasetInfo
)


class EVAL_FUNC_base(Protocol):
    def __call__(self, obj: EVAL_OBJECT) -> EVAL_OBJECT: ...


class EVAL_FUNC_get(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT: ...


class EVAL_FUNC_set(Protocol):
    def __call__(self, obj: EVAL_OBJECT, key: str, value: Any) -> EVAL_OBJECT: ...


EVAL_FUNC = EVAL_FUNC_base | EVAL_FUNC_get | EVAL_FUNC_set


def get_object(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, dict, ch.H5List)):
        raise EvalError(f"Cannot get object from '{type(obj).__name__}'")

    return obj[key]


def get_attribute(obj: EVAL_OBJECT, key: str) -> EVAL_OBJECT:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attribute from '{type(obj).__name__}'")

    return obj.attributes[key]


def get_keys(obj: EVAL_OBJECT) -> list[str]:
    if isinstance(obj, ch.H5Dict):
        return list(obj.keys())

    if isinstance(obj, ch.H5List):
        return [str(i) for i in range(len(obj))]

    raise EvalError(f"Cannot get keys from '{type(obj).__name__}'")


def get_attributes(obj: EVAL_OBJECT) -> dict[str, Any]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attributes from '{type(obj).__name__}'")

    return obj.attributes.as_dict()


def get_attribute_keys(obj: EVAL_OBJECT) -> list[str]:
    if not isinstance(obj, (ch.H5Dict, ch.Dataset)):
        raise EvalError(f"Cannot get attribute keys from '{type(obj).__name__}")

    return list(obj.attributes.keys())


def get_sizes_core(obj: ch.H5Dict, sizes: dict[str, Any], cum_size: int) -> tuple[int, dict[str, Any]]:
    for k, v in obj.items():
        if not isinstance(v, ch.H5Dict):
            if isinstance(v, str):
                v_size = sys.getsizeof(v)

            else:
                v_size = v.size * v.dtype.itemsize

            sizes[k] = nice_size_format(v_size)
            cum_size += v_size

        else:
            sub_cum_size, sub_sizes = get_sizes_core(v, {}, 0)
            sizes[k + f"['{nice_size_format(sub_cum_size)}']"] = sub_sizes
            cum_size += sub_cum_size

    return cum_size, sizes


def get_sizes(obj: EVAL_OBJECT) -> dict[str, Any]:
    if not isinstance(obj, ch.H5Dict):
        raise EvalError(f"Cannot get object sizes from '{type(obj).__name__}")

    cum_sum, sizes = get_sizes_core(obj, {}, 0)
    sizes["TOTAL"] = nice_size_format(cum_sum)

    return sizes


def set_key_value(obj: EVAL_OBJECT, key: str | int, value: Any) -> None:
    if not isinstance(obj, (ch.H5Dict, dict, ch.AttributeManager, DatasetInfo)):
        raise EvalError(f"Cannot assign value to '{type(obj).__name__}'")

    obj[key] = value


def del_object(obj: EVAL_OBJECT, key: str | int) -> None:
    if not isinstance(obj, (ch.H5Dict, dict, ch.AttributeManager, ch.H5List)):
        raise EvalError(f"Cannot delete value from '{type(obj).__name__}'")

    del obj[key]


def shallow_eval_statement(target: VTNode, context: EVAL_OBJECT) -> tuple[EVAL_OBJECT, str | int]:
    context, key = eval_statement(target.target, context), target.value
    assert isinstance(key, str | int), "invalid key type"

    if target.name == "GetAttr":
        if not isinstance(context, ch.H5Dict):
            raise EvalError(f"Cannot get attribute '{key}' from {type(context).__name__}")
        context = context.attributes

    return context, key


def create_dataset(
    data: EVAL_OBJECT | None,
    shape: tuple[int, ...] | None,
    dtype: str | None,
    chunks: bool,
    maxshape: bool | tuple[int | None, ...] | None,
) -> ch.AnonymousArrayCreationFunc:
    if shape is None:
        if data is None:
            shape = (0,)

        else:
            raise EvalError("TODO")

    match data:
        case None:
            shape = shape or (0,)
            dtype = dtype or "f"

            return ch.empty.defer(shape=shape, dtype=dtype, chunks=chunks, maxshape=maxshape)

        case 0:
            shape = shape or (1,)
            dtype = dtype or "f"

            return ch.zeros.defer(shape=shape, dtype=dtype, chunks=chunks, maxshape=maxshape)

        case 1:
            shape = shape or (1,)
            dtype = dtype or "f"

            return ch.ones.defer(shape=shape, dtype=dtype, chunks=chunks, maxshape=maxshape)

        case int(value):
            shape = shape or (1,)
            dtype = dtype or "f"

            return ch.ones.defer(shape=shape, dtype=dtype, chunks=chunks, maxshape=maxshape) * value

        case _:
            raise EvalError("TODO")


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

        case Node(name="Size"):
            context = get_sizes(context)

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
            del_object(context, value)

        case Node(name="Constant", value=value):
            context = value

        case Node(name="Dataset", data=data, shape=shape, dtype=dtype, chunks=chunks, maxshape=maxshape):
            data = None if data is None else eval_statement(data, context)
            context = create_dataset(data, shape, dtype, chunks, maxshape)

    return context


def eval(tree: Tree, context: EVAL_OBJECT) -> None:
    for statement in tree.body:
        context = eval_statement(statement, context)
