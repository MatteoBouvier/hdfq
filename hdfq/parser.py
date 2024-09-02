from __future__ import annotations

import functools
import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Iterator, Literal, cast

import hdfq
from hdfq.exceptions import (
    BinaryOpContext,
    ContextInfo,
    DatasetCreationContext,
    FunctionCallContext,
    GetStatementContext,
    ParseError,
)
from hdfq.lexer import Token, tokenize
from hdfq.syntax import Syntax
from hdfq.tokens import repr_tokens


class Special(str, Enum):
    context = "CTX"


@dataclass
class Node:
    name: str

    def __repr__(self) -> str:
        return f"{self.name}()"


@dataclass
class VNode(Node):
    value: str | int | float

    def __repr__(self) -> str:
        return f"{self.name}(value={self.value})"


@dataclass
class VTNode(Node):
    target: Literal[Special.context] | Node
    value: str | Node

    def __repr__(self) -> str:
        return f"{self.name}(target={self.target}, value={self.value})"

    def unwrap(self) -> tuple[Node | str, Node]:
        return self.target, VTNode(self.name, Special.context, self.value)


@dataclass
class DatasetNode(Node):
    data: str | Node | None
    shape: tuple[int, ...] | None
    dtype: str | None
    chunks: bool
    maxshape: bool | tuple[int | None, ...] | None


class Nodes(functools.partial[Node], Enum):
    Display = functools.partial(Node, "Display")
    Keys = functools.partial(Node, "Keys")
    Attrs = functools.partial(Node, "Attrs")
    AttrKeys = functools.partial(Node, "AttrKeys")
    Sizes = functools.partial(Node, "Size")
    Constant = functools.partial(VNode, "Constant")
    Get = functools.partial(VTNode, name="Get")
    GetAttr = functools.partial(VTNode, name="GetAttr")
    Assign = functools.partial(VTNode, name="Assign")
    Del = functools.partial(VTNode, name="Del")
    Dataset = functools.partial(DatasetNode, name="Dataset")


class Tree:
    def __init__(self, body: list[Node]) -> None:
        self.body = body

    def __repr__(self) -> str:
        return f"AST(\n\tbody={self.body}\n)"


def _all_int(tokens: list[Token]) -> bool:
    return bool(len(tokens)) and all(t.kind == Syntax.integer for t in tokens)


def match_atom(tokens: list[Token]) -> Node | None:
    match tokens:
        # match integer or str identifier
        case [Token(Syntax.integer, value=value)] | [Token(Syntax.identifier, value=value)]:
            return Nodes.Constant(value=value)

        # match float of type ".123"
        # case [hdfq.tokens.DOT, *right] if _all_int(right):
        #     return Nodes.Constant(value=float("." + "".join(str(t.value) for t in right)))

        # match float of type "123."
        case [*left, hdfq.tokens.DOT] if _all_int(left):
            return Nodes.Constant(value=float("".join(str(t.value) for t in left)))

    # match float of type "123.456"
    try:
        index = tokens.index(hdfq.tokens.DOT)
    except ValueError:
        return None

    left, right = tokens[:index], tokens[index + 1 :]
    if not _all_int(left) or not _all_int(right):
        return None

    return Nodes.Constant(value=float("".join(str(t.value) for t in left) + "." + "".join(str(t.value) for t in right)))


def pairwise(iterable: Iterable[Any]) -> Iterator[tuple[Any, Any]]:
    iterator = iter(iterable)
    first, second = None, next(iterator)

    for e in iterator:
        first = second
        second = e
        yield first, second


def split_at_commas(tokens: list[Token]) -> list[list[Token]]:
    if tokens[-1] != hdfq.tokens.COMMA:
        tokens.append(hdfq.tokens.COMMA)

    key = itertools.accumulate(
        [a == hdfq.tokens.COMMA and b.kind == Syntax.identifier for a, b in pairwise(tokens)], initial=False
    )
    return [list(group) for _, group in itertools.groupby(tokens, lambda _: next(key))]


def split_after_right_brackets(tokens: list[Token]) -> list[list[Token]]:
    return [
        list(group)
        for test, group in itertools.groupby(
            tokens, lambda t: t in (hdfq.tokens.RIGHT_PARENTHESIS, hdfq.tokens.RIGHT_ANGLE_BRACKET)
        )
        if not test
    ]


def match_shape(shape: tuple[int, ...] | None, tokens: list[Token], allow_none: bool = False) -> tuple[int, ...] | None:
    match tokens:
        case [hdfq.tokens.LEFT_PARENTHESIS, *shape_]:
            is_comma = [(s == hdfq.tokens.COMMA) if i % 2 else False for i, s in enumerate(shape_)]
            is_integer = [
                (isinstance(s.value, int) or allow_none and s.value is None) if not i % 2 else False
                for i, s in enumerate(shape_)
            ]

            if not all(c or i for c, i in zip(is_comma, is_integer)):
                raise ParseError(f"Got unexpected pattern ({repr_tokens(shape_)}) while trying to match a shape")

            if shape is not None:
                raise ParseError(f"Redefinition of dataset shape ({repr_tokens(shape_)}), previous shape was {shape}")

            return tuple(cast(int, s.value) for i, s in enumerate(shape_) if not i % 2)

        case _:
            return shape


def match_dtype(dtype: str | None, tokens: list[Token]) -> str | None:
    match tokens:
        case [hdfq.tokens.LEFT_ANGLE_BRACKET, Token(Syntax.identifier, value=value)]:
            if not isinstance(value, str):
                raise ParseError(f"Got unexpected value '{value}' for data type", context=DatasetCreationContext())

            if dtype is not None:
                raise ParseError(f"Redefinition of data type {value}, previous shape was {dtype}")

            return value

        case _:
            return dtype


def match_dataset(tokens: list[Token]) -> DatasetNode | None:
    try:
        rb_index = tokens.index(hdfq.tokens.RIGHT_BRACKET)
    except ValueError:
        return None

    data, parameters = tokens[:rb_index], tokens[rb_index + 1 :]

    match data:
        case [hdfq.tokens.LEFT_BRACKET]:
            dataset = cast(DatasetNode, Nodes.Dataset(data=None, shape=None, dtype=None, chunks=True, maxshape=None))

        case [hdfq.tokens.LEFT_BRACKET, *content]:
            data_part, *details = split_at_commas(content)

            data = match_atom(data_part[:-1]) or match_get_statement(data_part[:-1])  # :-1 because of trailing commas
            if data is None:
                raise ParseError(f"Got unexpected pattern {repr_tokens(data_part)}", context=DatasetCreationContext())

            dataset = cast(DatasetNode, Nodes.Dataset(data=data, shape=None, dtype=None, chunks=True, maxshape=None))

            for detail in details:
                match detail:
                    case [
                        Token(Syntax.identifier, value="chunks"),
                        hdfq.tokens.EQUAL,
                        Token(Syntax.boolean, value=boolean),
                        hdfq.tokens.COMMA,
                    ]:
                        dataset.chunks = cast(bool, boolean)

                    case [
                        Token(Syntax.identifier, value="maxshape"),
                        hdfq.tokens.EQUAL,
                        Token(Syntax.boolean, value=maxshape),
                        hdfq.tokens.RIGHT_PARENTHESIS,
                        hdfq.tokens.COMMA,
                    ]:
                        assert isinstance(maxshape, bool)
                        dataset.maxshape = maxshape

                    case [
                        Token(Syntax.identifier, value="maxshape"),
                        hdfq.tokens.EQUAL,
                        *shape,
                        hdfq.tokens.RIGHT_PARENTHESIS,
                        hdfq.tokens.COMMA,
                    ]:
                        maxshape = match_shape(None, shape, allow_none=True)
                        if maxshape is None:
                            raise ParseError("TODO")

                        dataset.maxshape = maxshape

                    case _:
                        raise ParseError("TODO")

        case _:
            return None

    shape, dtype = None, None
    for parameter in split_after_right_brackets(parameters):
        shape = match_shape(shape, parameter)
        dtype = match_dtype(dtype, parameter)

    dataset.shape = shape
    dataset.dtype = dtype
    return dataset


def matches_whole(tokens: list[Token], allow_empty: bool) -> bool:
    match tokens:
        case []:
            return allow_empty

        case [hdfq.tokens.DOT]:
            return True

        case _:
            return False


def match_get_object(tokens: list[Token], *, allow_get_attr: bool, context: ContextInfo | None) -> VTNode:
    match tokens:
        case [*left, hdfq.tokens.DOT, Token(Syntax.identifier | Syntax.integer, value=value)]:
            target = match_get_statement(left, context=context) if len(left) else Special.context
            return cast(VTNode, Nodes.Get(target=target, value=value))

        case [*left, hdfq.tokens.OCTOTHORPE, Token(Syntax.identifier, value=value)]:
            if not allow_get_attr:
                if isinstance(context, GetStatementContext):
                    context.first = value
                raise ParseError("Cannot get attribute ", context=context)

            if context is None:
                context = GetStatementContext(second=str(value))
            target = match_get_statement(left, allow_get_attr=False, context=context) if len(left) else Special.context
            return cast(VTNode, Nodes.GetAttr(target=target, value=value))

        case _:
            raise ParseError(f"Got unexpected pattern {repr_tokens(tokens)}", context=context)


def match_get_statement(
    tokens: list[Token], *, allow_get_attr: bool = True, context: ContextInfo | None = None
) -> VTNode:
    return match_get_object(tokens, allow_get_attr=allow_get_attr, context=context)


def match_get_statement_all(
    tokens: list[Token], *, allow_empty: bool = False, context: BinaryOpContext | None = None
) -> Node | None:
    if matches_whole(tokens, allow_empty=allow_empty):
        return None

    return match_get_statement(tokens, context=context)


def match_assignment(tokens: list[Token]) -> Node | None:
    try:
        assign_index = tokens.index(hdfq.tokens.EQUAL)
    except ValueError:
        return None

    left, right = tokens[:assign_index], tokens[assign_index + 1 :]
    return Nodes.Assign(
        target=match_get_statement_all(left, context=BinaryOpContext("assignment", "left")),
        value=match_atom(right)
        or match_dataset(right)
        or match_get_statement_all(right, context=BinaryOpContext("assignment", "right")),
    )


def match_descriptor(tokens: list[Token]) -> Node | None:
    match tokens:
        case [hdfq.tokens.KEYS]:
            return Nodes.Keys()

        case [hdfq.tokens.ATTRIBUTES]:
            return Nodes.Attrs()

        case [hdfq.tokens.ATTRIBUTE_KEYS]:
            return Nodes.AttrKeys()

        case [hdfq.tokens.SIZES]:
            return Nodes.Sizes()

        case _:
            return None


def match_function_call(tokens: list[Token]) -> Node | None:
    match tokens:
        case [hdfq.tokens.DEL, hdfq.tokens.LEFT_PARENTHESIS, *argument, hdfq.tokens.RIGHT_PARENTHESIS]:
            target, value = match_get_statement(argument, context=FunctionCallContext("del")).unwrap()
            return Nodes.Del(target=target, value=value)

        case _:
            return None


def match_statement(tokens: list[Token]) -> tuple[Node | None, bool]:
    node = match_assignment(tokens) or match_function_call(tokens)
    if node is not None:
        return node, True

    return (match_descriptor(tokens) or match_get_statement_all(tokens, allow_empty=True)), False


def split_at_pipes(tokens: list[Token]) -> Iterator[list[Token]]:
    try:
        index = tokens.index(hdfq.tokens.PIPE)
        yield tokens[:index]
        yield from split_at_pipes(tokens[index + 1 :])

    except ValueError:
        yield tokens


def match_statements(tokens: list[Token]) -> tuple[list[Node], bool]:
    statements: list[Node] = []
    requires_write_access = False

    for statement in split_at_pipes(tokens):
        matched_statement, is_write_operation = match_statement(statement)
        if matched_statement is not None:
            statements.append(matched_statement)
            requires_write_access = requires_write_access or is_write_operation

    return statements, requires_write_access


def parse(filter: str) -> tuple[Tree, bool]:
    tokens = list(tokenize(filter))
    nodes, requires_write_access = match_statements(tokens)

    return Tree(body=nodes + [Nodes.Display()]), requires_write_access
