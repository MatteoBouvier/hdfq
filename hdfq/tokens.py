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

DOT = Token(Syntax.dot)
EQUAL = Token(Syntax.equal)
OCTOTHORPE = Token(Syntax.octothorpe)
LEFT_PARENTHESIS = Token(Syntax.left_parenthesis)
RIGHT_PARENTHESIS = Token(Syntax.right_parenthesis)
PIPE = Token(Syntax.pipe)

INT = functools.partial(Token, Syntax.integer)
FLOAT = functools.partial(Token, Syntax.floating)
IDENTIFIER = functools.partial(Token, Syntax.identifier)


def repr_tokens(tokens: list[Token]) -> str:
    return '"' + "".join(map(lambda x: x.short_repr(), tokens)) + '"'
