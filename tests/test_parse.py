import pytest

from hdfq.exceptions import ParseError
from hdfq.parser import Nodes, Special, parse


def test_parse_get_whole():
    tree, _ = parse(".")
    assert tree.body == [Nodes.Display()]

    tree, _ = parse("")
    assert tree.body == [Nodes.Display()]


def test_parse_get_object():
    tree, _ = parse(".a")
    assert tree.body == [Nodes.Get(target=Special.context, value="a"), Nodes.Display()]


def test_parse_get_nested_object():
    tree, _ = parse(".a.b")
    assert tree.body == [Nodes.Get(target=Nodes.Get(target=Special.context, value="a"), value="b"), Nodes.Display()]


def test_parse_get_attribute():
    tree, _ = parse("#some_attr")
    assert tree.body == [Nodes.GetAttr(target=Special.context, value="some_attr"), Nodes.Display()]


def test_parse_get_attr_from_attr_should_error():
    with pytest.raises(ParseError):
        parse("#a#b")


def test_parse_value_assignment():
    tree, _ = parse(".b = -1")
    assert tree.body == [
        Nodes.Assign(target=Nodes.Get(target=Special.context, value="b"), value=Nodes.Constant(-1)),
        Nodes.Display(),
    ]


def test_parse_attr_assignment():
    tree, _ = parse("#c = 'test'")
    assert tree.body == [
        Nodes.Assign(target=Nodes.GetAttr(target=Special.context, value="c"), value=Nodes.Constant("test")),
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
    assert tree[0].body == [Nodes.Keys(), Nodes.Display()]


def test_parse_function_call():
    tree, _ = parse("del(.a)")
    assert tree.body == [
        Nodes.Del(target=Special.context, value=Nodes.Get(target=Special.context, value="a")),
        Nodes.Display(),
    ]


def test_parse_function_call_nested():
    tree, _ = parse("del(.a.b.c)")
    assert tree.body == [
        Nodes.Del(
            target=Nodes.Get(target=Nodes.Get(target=Special.context, value="a"), value="b"),
            value=Nodes.Get(target=Special.context, value="c"),
        ),
        Nodes.Display(),
    ]


def test_parse_multiple_statements():
    tree, _ = parse(".obj | keys")
    assert tree.body == [Nodes.Get(target=Special.context, value="obj"), Nodes.Keys(), Nodes.Display()]


@pytest.mark.parametrize(
    "pattern,expected",
    [
        (
            "[]",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(data=None, shape=None, dtype=None, chunks=True, maxshape=None),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[0]",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Constant(value=0), shape=None, dtype=None, chunks=True, maxshape=None
                    ),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[.b]",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Get(target=Special.context, value="b"),
                        shape=None,
                        dtype=None,
                        chunks=True,
                        maxshape=None,
                    ),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[0](10, 20)",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Constant(value=0),
                        shape=(10, 20),
                        dtype=None,
                        chunks=True,
                        maxshape=None,
                    ),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[0](10, 20)<f>",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Constant(value=0),
                        shape=(10, 20),
                        dtype="f",
                        chunks=True,
                        maxshape=None,
                    ),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[0, chunks=false, maxshape=(50, 50)](10, 20)<f>",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Constant(value=0),
                        shape=(10, 20),
                        dtype="f",
                        chunks=False,
                        maxshape=(50, 50),
                    ),
                ),
                Nodes.Display(),
            ],
        ),
        (
            "[0, chunks=false, maxshape=(50, None)](10, 20)<f>",
            [
                Nodes.Assign(
                    target=Nodes.Get(target=Special.context, value="a"),
                    value=Nodes.Dataset(
                        data=Nodes.Constant(value=0),
                        shape=(10, 20),
                        dtype="f",
                        chunks=False,
                        maxshape=(50, None),
                    ),
                ),
                Nodes.Display(),
            ],
        ),
    ],
)
def test_parse_dataset_creation(pattern, expected):
    tree, _ = parse(".a = " + pattern)
    assert tree.body == expected


def test_parse_identifier_as_integer():
    tree, _ = parse(".a.3")
    assert tree.body == [Nodes.Get(target=Nodes.Get(target=Special.context, value="a"), value=3), Nodes.Display()]
