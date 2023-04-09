import typing
from functools import cached_property
from itertools import zip_longest

from returns import returns
from unicodedata import east_asian_width


class StringWidthCalculator:
    EAST_ASIAN_WIDTH = {
        'Na': 1,
        'W': 2,
    }

    @classmethod
    def get_character_width(cls, char: str) -> int:
        return cls.EAST_ASIAN_WIDTH[east_asian_width(char)]

    @classmethod
    @returns(sum)
    def get(cls, s: str) -> int:
        for char in s:
            yield cls.get_character_width(char)


string_width = StringWidthCalculator.get


class TableColumn:
    def __init__(self, name: str, *, formatter=None):
        self.name = name
        if formatter is None:
            formatter = str
        self._formatter = formatter
        self._width = string_width(name)

    def render(self, value) -> str:
        if value is None:
            value_s = ''
        else:
            value_s = self._formatter(value)
        self._width = max(self._width, string_width(value_s))
        return value_s

    def format(self, s: str) -> str:
        return s + ' ' * (self._width - string_width(s))


class TableColumns:
    def __init__(self, *, formatters=None):
        self._columns: list[TableColumn] = []
        if formatters is None:
            formatters = {}
        self._formatters = formatters

    def __contains__(self, name: str) -> bool:
        for col in self._columns:
            if col.name == name:
                return True
        return False

    @returns(list)
    def render(self, item: dict) -> list[str]:
        for col in self._columns:
            value = item.get(col.name)
            yield col.render(value)
        for name, value in item.items():
            if name in self:
                continue
            col = TableColumn(name, formatter=self._formatters.get(name))
            self._columns.append(col)
            yield col.render(value)

    @returns(lambda s: s.strip())
    @returns(' | '.join)
    def format(self, row: typing.Iterable[str]) -> str:
        yield ''
        for col, elem in zip_longest(self._columns, row, fillvalue=''):
            yield col.format(elem)
        yield ''

    def __str__(self) -> str:
        return self.format(col.name for col in self._columns)


class RenderTable:
    def __init__(
            self,
            data: typing.Iterable[dict],
            *,
            formatters=None,
    ):
        self._data = iter(data)
        self._columns = TableColumns(formatters=formatters)

    @cached_property
    @returns(list)
    def _rendered_data(self) -> list[list[str]]:
        for item in self._data:
            yield self._columns.render(item)

    @cached_property
    @returns('\n'.join)
    def _s(self) -> str:
        _ = self._rendered_data
        yield str(self._columns)
        for row in self._rendered_data:
            yield self._columns.format(row)

    def __str__(self) -> str:
        return self._s
