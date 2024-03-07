from hq.parse import Nodes, parse


def test_parse_get_whole():
    tree = parse(".")
    assert tree.body == [Nodes.Display]

    tree = parse("")
    assert tree.body == [Nodes.Display]


def test_parse_get_object():
    tree = parse(".a")
    assert tree.body == [Nodes.Get.with_args("a"), Nodes.Display]


def test_parse_get_attribute():
    tree = parse("#some_attr")
    assert tree.body == [Nodes.Attr_get.with_args("some_attr"), Nodes.Display]


def test_parse_get_and_keys():
    tree = parse(".obj | keys")
    assert tree.body == [Nodes.Get.with_args("obj"), Nodes.Keys, Nodes.Display]


def test_parse_set_value():
    tree = parse(".b = -1")
    assert tree.body == [Nodes.Set.with_args("b", "-1"), Nodes.Display]


def test_paser_set_str_value():
    tree = parse("#c = 'test'")
    assert tree.body == [Nodes.Attr_set.with_args("c", "'test'"), Nodes.Display]
