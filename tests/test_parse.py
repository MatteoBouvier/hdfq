import pytest

from hq.exceptions import ParseError
from hq.parser import Nodes, parse


def test_parse_get_whole():
    tree = parse(".")
    assert tree.body == [Nodes.Display()]

    tree = parse("")
    assert tree.body == [Nodes.Display()]


def test_parse_get_object():
    tree = parse(".a")
    assert tree.body == [Nodes.Get(target="INPUT", value="a"), Nodes.Display()]


def test_parse_get_nested_object():
    tree = parse(".a.b")
    assert tree.body == [Nodes.Get(target=Nodes.Get(target="INPUT", value="a"), value="b"), Nodes.Display()]


def test_parse_get_attribute():
    tree = parse("#some_attr")
    assert tree.body == [Nodes.GetAttr(target="INPUT", value="some_attr"), Nodes.Display()]


def test_parse_get_attr_from_attr_should_error():
    with pytest.raises(ParseError):
        parse("#a#b")


def test_parse_value_assignment():
    tree = parse(".b = -1")
    assert tree.body == [
        Nodes.Assign(target=Nodes.Get(target="INPUT", value="b"), value=Nodes.Constant(-1)),
        Nodes.Display(),
    ]


def test_parse_attr_assignment():
    tree = parse("#c = 'test'")
    assert tree.body == [
        Nodes.Assign(target=Nodes.GetAttr(target="INPUT", value="c"), value=Nodes.Constant("test")),
        Nodes.Display(),
    ]


def test_parse_invalid_assignment():
    with pytest.raises(ParseError):
        parse("1 = 2")


def test_parse_invalid_empty_assignment():
    with pytest.raises(ParseError):
        parse(".b = ")


def test_parse_descriptor():
    tree = parse("keys")
    assert tree.body == [Nodes.Keys(), Nodes.Display()]


def test_parse_function_call():
    tree = parse("del(.a)")
    assert tree.body == [
        Nodes.Del(target="INPUT", value=Nodes.Get(target="INPUT", value="a")),
        Nodes.Display(),
    ]


def test_parse_function_call_nested():
    tree = parse("del(.a.b.c)")
    assert tree.body == [
        Nodes.Del(
            target=Nodes.Get(target=Nodes.Get(target="INPUT", value="a"), value="b"),
            value=Nodes.Get(target="INPUT", value="c"),
        ),
        Nodes.Display(),
    ]


def test_parse_multiple_statements():
    tree = parse(".obj | keys")
    assert tree.body == [Nodes.Get(target="INPUT", value="obj"), Nodes.Keys(), Nodes.Display()]
