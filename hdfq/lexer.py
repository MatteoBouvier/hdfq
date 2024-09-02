import re
from typing import Iterable

from hdfq import tokens
from hdfq.syntax import Syntax
from hdfq.tokens import Token


def is_int(string: str) -> bool:
    if string[0] in ("-", "+"):
        return string[1:].isdigit()
    return string.isdigit()


def is_bool(string: str) -> bool:
    return string.lower() in ("true", "false")


def lex(string: str) -> Token:
    if is_int(string):
        return tokens.INT(value=int(string))

    if is_bool(string):
        return tokens.BOOLEAN(value=eval(string.capitalize()))

    match string:
        case Syntax.keys:
            return tokens.KEYS

        case Syntax.attributes:
            return tokens.ATTRIBUTES

        case Syntax.attribute_keys:
            return tokens.ATTRIBUTE_KEYS

        case Syntax.sizes:
            return tokens.SIZES

        case Syntax.del_:
            return tokens.DEL

    if string.capitalize() == Syntax.none:
        return tokens.NONE

    string = string.replace('"', "").replace("'", "")
    if string.isidentifier():
        return tokens.IDENTIFIER(value=string)

    match string:
        case Syntax.dot:
            return tokens.DOT

        case Syntax.comma:
            return tokens.COMMA

        case Syntax.equal:
            return tokens.EQUAL

        case Syntax.octothorpe:
            return tokens.OCTOTHORPE

        case Syntax.left_parenthesis:
            return tokens.LEFT_PARENTHESIS

        case Syntax.right_parenthesis:
            return tokens.RIGHT_PARENTHESIS

        case Syntax.left_bracket:
            return tokens.LEFT_BRACKET

        case Syntax.right_bracket:
            return tokens.RIGHT_BRACKET

        case Syntax.left_angle_bracket:
            return tokens.LEFT_ANGLE_BRACKET

        case Syntax.right_angle_bracket:
            return tokens.RIGHT_ANGLE_BRACKET

        case Syntax.pipe:
            return tokens.PIPE

        case _:
            raise SyntaxError(f"Syntax error at : '{string}'")


def tokenize(string: str) -> Iterable[Token]:
    for s in filter(None, re.split(r"([^a-zA-Z0-9_'\"-])", string.replace(" ", ""))):
        yield lex(s)
