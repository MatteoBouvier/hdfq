import functools
from typing import NamedTuple

from hdfq.syntax import Syntax


class Token(NamedTuple):
    kind: Syntax
    value: str | int | float | None = None

    def __repr__(self) -> str:
        if self.value is None:
            return f"Token<{self.kind}>"
        return f"Token<{self.kind}={self.value}>"

    def short_repr(self) -> str:
        return str(self.kind.value) if self.value is None else str(self.value)


KEYS = Token(Syntax.keys)
ATTRIBUTES = Token(Syntax.attributes)
ATTRIBUTE_KEYS = Token(Syntax.attribute_keys)
SIZES = Token(Syntax.sizes)
DEL = Token(Syntax.del_)
NONE = Token(Syntax.none)

DOT = Token(Syntax.dot)
COMMA = Token(Syntax.comma)
EQUAL = Token(Syntax.equal)
OCTOTHORPE = Token(Syntax.octothorpe)
LEFT_PARENTHESIS = Token(Syntax.left_parenthesis)
RIGHT_PARENTHESIS = Token(Syntax.right_parenthesis)
LEFT_BRACKET = Token(Syntax.left_bracket)
RIGHT_BRACKET = Token(Syntax.right_bracket)
LEFT_ANGLE_BRACKET = Token(Syntax.left_angle_bracket)
RIGHT_ANGLE_BRACKET = Token(Syntax.right_angle_bracket)
PIPE = Token(Syntax.pipe)

BOOLEAN = functools.partial(Token, Syntax.boolean)
INT = functools.partial(Token, Syntax.integer)
IDENTIFIER = functools.partial(Token, Syntax.identifier)


def repr_tokens(tokens: list[Token]) -> str:
    return '"' + "".join(map(lambda x: x.short_repr(), tokens)) + '"'
