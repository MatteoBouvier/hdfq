from enum import Enum


class Syntax(str, Enum):
    # Keywords ------------------------
    keys = "keys"
    attributes = "attrs"
    attribute_keys = "kattrs"
    del_ = "del"

    # Punctuation ---------------------
    dot = "."
    equal = "="
    octothorpe = "#"
    left_parenthesis = "("
    right_parenthesis = ")"
    pipe = "|"

    # Literal -------------------------
    integer = "int"
    floating = "float"
    identifier = "identifier"
