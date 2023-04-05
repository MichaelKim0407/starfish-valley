import dataclasses
import json
import typing
from collections import defaultdict
from functools import cached_property

from returns import returns


class Merge:
    def __init__(
            self,
            levels: int = 1,
            *,
            dedup_key=None,
    ):
        self.levels = levels
        self.dedup_key = dedup_key

    @cached_property
    def _next(self) -> typing.Self:
        return self.__class__(self.levels - 1)

    def __call__(self, iterable):
        if self.levels <= 0:
            return list(iterable)

        result = defaultdict(list)
        seen = defaultdict(set)

        for key, value in iterable:
            if self.dedup_key is not None:
                dup_key = self.dedup_key(value)
                if dup_key in seen[key]:
                    continue
                else:
                    seen[key].add(dup_key)

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


class JSONEncoder(json.JSONEncoder):
    # https://stackoverflow.com/a/51286749/3248736
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
