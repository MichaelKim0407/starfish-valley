from collections import defaultdict

from returns import returns


def skip_empty_values(iterable):
    for key, value in iterable:
        if not value:
            continue
        yield key, value


def merge(iterable):
    result = defaultdict(list)
    for key, value in iterable:
        result[key].append(value)
    return dict(result)


@returns(tuple)
def game_version_sort_key(game_version: str) -> tuple[int, ...]:
    for elem in game_version.split('.'):
        yield int(elem)


@returns(list)
def convert_items(items, converter) -> list:
    for item in items:
        yield converter(item)
