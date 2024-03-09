import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


def myexcepthook(type, value, _):
    print(f"hq: {type.__name__}: {value}")


sys.excepthook = myexcepthook


@dataclass
class ContextInfo(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass


@dataclass
class GetStatementContext(ContextInfo):
    second: str
    _first: str | None = None

    def __repr__(self) -> str:
        assert self.first is not None
        return f'"{self.second}" of attribute "{self.first}"'

    @property
    def first(self) -> str | None:
        return self._first

    @first.setter
    def first(self, value):
        self._first = value


@dataclass
class BinaryOpContext(ContextInfo):
    kind: Literal["assignment"]
    side: Literal["left", "right"]

    def __repr__(self) -> str:
        return f" while parsing {self.side} hand side of {self.kind}"


@dataclass
class FunctionCallContext(ContextInfo):
    kind: Literal["del"]

    def __repr__(self) -> str:
        return f" while parsing arguments of {self.kind} function"


class ParseError(Exception):
    def __init__(self, msg: str = "", context: ContextInfo | None = None) -> None:
        super().__init__(msg)
        self.msg = msg
        self.context = context

    def _str_context(self) -> str:
        return "" if self.context is None else repr(self.context)

    def __str__(self) -> str:
        return f"{self.msg}{self._str_context()}"


class EvalError(Exception):
    pass
