from hdfq.lexer import Token, tokenize
from hdfq.syntax import Syntax


def test_lex_empty_pattern():
    assert list(tokenize("")) == []


def test_lex_get_object():
    assert list(tokenize(".a")) == [Token(Syntax.dot), Token(Syntax.identifier, "a")]


def test_lex_del():
    assert list(tokenize("del(.a.b#c)")) == [
        Token(Syntax.del_),
        Token(Syntax.left_parenthesis),
        Token(Syntax.dot),
        Token(Syntax.identifier, "a"),
        Token(Syntax.dot),
        Token(Syntax.identifier, "b"),
        Token(Syntax.octothorpe),
        Token(Syntax.identifier, "c"),
        Token(Syntax.right_parenthesis),
    ]


def test_lex_pipe():
    assert list(tokenize(".a | keys")) == [
        Token(Syntax.dot),
        Token(Syntax.identifier, "a"),
        Token(Syntax.pipe),
        Token(Syntax.keys),
    ]


def test_lex_size():
    assert list(tokenize(".a | sizes")) == [
        Token(Syntax.dot),
        Token(Syntax.identifier, "a"),
        Token(Syntax.pipe),
        Token(Syntax.sizes),
    ]
