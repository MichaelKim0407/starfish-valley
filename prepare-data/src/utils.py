import typing
from collections import defaultdict
from functools import cached_property

from returns import returns


class Merge:
    def __init__(self, levels: int = 1):
        self.levels = levels

    @cached_property
    def _next(self) -> typing.Self:
        return self.__class__(self.levels - 1)

    def __call__(self, iterable):
        if self.levels <= 0:
            return list(iterable)

        result = defaultdict(list)
        for key, value in iterable:
            result[key].append(value)
        return {
            key: self._next(values)
            for key, values in result.items()
        }


merge = Merge(1)


@returns(tuple)
def game_version_sort_key(game_version: str) -> tuple[int, ...]:
    for elem in game_version.split('.'):
        yield int(elem)


@returns(list)
def convert_items(items, converter) -> list:
    for item in items:
        yield converter(item)
