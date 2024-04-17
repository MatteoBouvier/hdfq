from __future__ import annotations

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Literal, cast

import hdfq
from hdfq.exceptions import BinaryOpContext, ContextInfo, FunctionCallContext, GetStatementContext, ParseError
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


class Tree:
    def __init__(self, body: list[Node]) -> None:
        self.body = body

    def __repr__(self) -> str:
        return f"AST(\n\tbody={self.body}\n)"


def match_atom(tokens: list[Token]) -> Node | None:
    match tokens:
        case (
            [Token(Syntax.integer, value=value)]
            | [Token(Syntax.floating, value=value)]
            | [Token(Syntax.identifier, value=value)]
        ):
            return Nodes.Constant(value=value)

        case _:
            return None


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
        case [*left, hdfq.tokens.DOT, Token(Syntax.identifier, value=value)]:
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
        value=match_atom(right) or match_get_statement_all(right, context=BinaryOpContext("assignment", "right")),
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
