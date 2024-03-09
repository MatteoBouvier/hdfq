import re
from typing import Iterable

from hq import tokens
from hq.syntax import Syntax
from hq.tokens import Token


def is_int(string: str) -> bool:
    if string[0] in ("-", "+"):
        return string[1:].isdigit()
    return string.isdigit()


def is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


def lex(string: str) -> Token:
    if is_int(string):
        return tokens.INT(value=int(string))

    if is_float(string):
        return tokens.FLOAT(value=float(string))

    match string:
        case Syntax.keys:
            return tokens.KEYS

        case Syntax.attributes:
            return tokens.ATTRIBUTES

        case Syntax.attribute_keys:
            return tokens.ATTRIBUTE_KEYS

        case Syntax.del_:
            return tokens.DEL

    string = string.replace('"', "").replace("'", "")
    if string.isidentifier():
        return tokens.IDENTIFIER(value=string)

    match string:
        case Syntax.dot:
            return tokens.DOT

        case Syntax.equal:
            return tokens.EQUAL

        case Syntax.octothorpe:
            return tokens.OCTOTHORPE

        case Syntax.left_parenthesis:
            return tokens.LEFT_PARENTHESIS

        case Syntax.right_parenthesis:
            return tokens.RIGHT_PARENTHESIS

        case Syntax.pipe:
            return tokens.PIPE

        case _:
            raise SyntaxError(f"Syntax error at : '{string}'")


def tokenize(string: str) -> Iterable[Token]:
    for s in filter(None, re.split(r"([^a-zA-Z0-9_'\"-])", string.replace(" ", ""))):
        yield lex(s)
