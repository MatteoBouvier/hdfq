from __future__ import annotations

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Literal, cast

import hq
from hq.exceptions import ParseError
from hq.lexer import Token, tokenize
from hq.syntax import Syntax
from hq.tokens import repr_tokens


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

        case [hq.tokens.DOT]:
            return True

        case _:
            return False


def match_get_object(tokens: list[Token]) -> VTNode:
    match tokens:
        case [*left, hq.tokens.DOT, Token(Syntax.identifier, value=value)]:
            target = match_get_statement(left) if len(left) else Special.context
            return cast(VTNode, Nodes.Get(target=target, value=value))

        case _:
            raise ParseError(f"Got unexpected pattern : {repr_tokens(tokens)}")


def match_get_attribute(tokens: list[Token]) -> VTNode:
    match tokens:
        case [*left, hq.tokens.OCTOTHORPE, Token(Syntax.identifier, value=value)]:
            target = match_get_statement(left, allow_get_attr=False) if len(left) else Special.context
            return cast(VTNode, Nodes.GetAttr(target=target, value=value))

        case _:
            raise ParseError(f"Got unexpected pattern : {repr_tokens(tokens)}")


def match_get_statement(tokens: list[Token], allow_get_attr: bool = True) -> VTNode:
    if allow_get_attr:
        try:
            return match_get_attribute(tokens)
        except ParseError:
            pass

    return match_get_object(tokens)


def match_get_statement_all(tokens: list[Token], allow_empty: bool = False) -> Node | None:
    if matches_whole(tokens, allow_empty=allow_empty):
        return None

    return match_get_statement(tokens)


def match_assignment(tokens: list[Token]) -> Node | None:
    try:
        assign_index = tokens.index(hq.tokens.EQUAL)
    except ValueError:
        return None

    left, right = tokens[:assign_index], tokens[assign_index + 1 :]
    return Nodes.Assign(target=match_get_statement_all(left), value=match_atom(right) or match_get_statement_all(right))


def match_descriptor(tokens: list[Token]) -> Node | None:
    match tokens:
        case [hq.tokens.KEYS]:
            return Nodes.Keys()

        case [hq.tokens.ATTRIBUTES]:
            return Nodes.Attrs()

        case [hq.tokens.ATTRIBUTE_KEYS]:
            return Nodes.AttrKeys()

        case _:
            return None


def match_function_call(tokens: list[Token]) -> Node | None:
    match tokens:
        case [hq.tokens.DEL, hq.tokens.LEFT_PARENTHESIS, *argument, hq.tokens.RIGHT_PARENTHESIS]:
            target, value = match_get_statement(argument).unwrap()
            return Nodes.Del(target=target, value=value)

        case _:
            return None


def match_statement(tokens: list[Token]) -> Node | None:
    return (
        match_assignment(tokens)
        or match_descriptor(tokens)
        or match_function_call(tokens)
        or match_get_statement_all(tokens, allow_empty=True)
    )


def split_at_pipes(tokens: list[Token]) -> Iterator[list[Token]]:
    try:
        index = tokens.index(hq.tokens.PIPE)
        yield tokens[:index]
        yield from split_at_pipes(tokens[index + 1 :])

    except ValueError:
        yield tokens


def match_statements(tokens: list[Token]) -> list[Node]:
    statements: list[Node] = []

    for statement in split_at_pipes(tokens):
        matched_statement = match_statement(statement)
        if matched_statement is not None:
            statements.append(matched_statement)

    return statements


def parse(pattern: str) -> Tree:
    tokens = list(tokenize(pattern))
    nodes = match_statements(tokens)

    return Tree(body=nodes + [Nodes.Display()])
