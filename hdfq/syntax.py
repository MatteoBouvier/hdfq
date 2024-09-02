from enum import Enum


class Syntax(str, Enum):
    # Keywords ------------------------
    keys = "keys"
    attributes = "attrs"
    attribute_keys = "kattrs"
    sizes = "sizes"
    del_ = "del"
    none = "None"

    # Punctuation ---------------------
    dot = "."
    comma = ","
    equal = "="
    octothorpe = "#"
    left_parenthesis = "("
    right_parenthesis = ")"
    left_bracket = "["
    right_bracket = "]"
    left_angle_bracket = "<"
    right_angle_bracket = ">"
    pipe = "|"

    # Literal -------------------------
    boolean = "boolean"
    integer = "int"
    identifier = "identifier"
